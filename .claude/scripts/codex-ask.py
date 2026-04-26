#!/usr/bin/env python3
"""Codex Ask - CLI tool for Claude to get Codex opinion on any task.

Usage:
    py -3 .claude/scripts/codex-ask.py "Your question or task description"

Connects to warm Codex broker (ws://127.0.0.1:4500), sends question,
waits for response, prints to stdout. Claude reads the output.

Works everywhere: main session, subtasks, Agent Teams, pipeline phases.
If broker is not running, falls back to codex exec.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Also update last-consulted for codex-broker sync
BROKER_URL = "ws://127.0.0.1:4500"

if sys.platform == "win32":
    for s in [sys.stdin, sys.stdout, sys.stderr]:
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")

BROKER_URL = "ws://127.0.0.1:4500"
INACTIVITY_TIMEOUT = 30
MAX_TIMEOUT = 300

logger = logging.getLogger(__name__)


def parse_codex_exec_stdout(stdout: str) -> str | None:
    """Parse Codex CLI exec stdout. Handles both:

      - v0.117 (legacy): header lines + sentinel ``codex`` line + response
        + ``tokens used N`` trailer, all in stdout. Extract body between
        the ``codex`` sentinel and the ``tokens used`` trailer.
      - v0.125 (modern): header is sent to stderr, only the response (and
        an optional ``tokens used`` trailer) appears in stdout. No
        sentinel - return everything until the trailer (or all of it if
        no trailer is present).

    Returns the response text, or ``None`` when stdout is empty / blank /
    yields no parseable body.
    """
    logger.info("parse_codex_exec_stdout.enter stdout_len=%d", len(stdout or ""))
    if not stdout or not stdout.strip():
        logger.info("parse_codex_exec_stdout.exit result_truthy=False reason=empty")
        return None
    lines = stdout.splitlines()
    # Try v0.117 sentinel-based extraction first (more specific contract).
    if any(line.strip() == "codex" for line in lines):
        in_resp = False
        out: list[str] = []
        for line in lines:
            if not in_resp:
                if line.strip() == "codex":
                    in_resp = True
                continue
            if "tokens used" in line:
                break
            out.append(line)
        result = "\n".join(out).strip()
        if result:
            logger.info("parse_codex_exec_stdout.exit result_truthy=True format=v0.117")
            return result
    # v0.125 fallback: take everything up to (optional) "tokens used" trailer.
    out2: list[str] = []
    for line in lines:
        if line.strip() == "tokens used":
            break
        out2.append(line)
    result2 = "\n".join(out2).strip()
    truthy = bool(result2)
    logger.info("parse_codex_exec_stdout.exit result_truthy=%s format=v0.125", truthy)
    return result2 or None


def ask_via_broker(prompt):
    """Ask Codex via warm WebSocket broker."""
    from websockets.sync.client import connect

    t0 = time.time()
    ws = connect(BROKER_URL, close_timeout=5, open_timeout=5)

    # Initialize
    ws.send(json.dumps({"id": 1, "method": "initialize", "params": {
        "clientInfo": {"title": "Codex Ask", "name": "codex-ask", "version": "1.0.0"},
        "capabilities": {
            "experimentalApi": False,
            "optOutNotificationMethods": [
                "item/agentMessage/delta",
                "item/reasoning/summaryTextDelta",
                "item/reasoning/summaryPartAdded",
                "item/reasoning/textDelta",
            ],
        },
    }}))
    ws.recv()
    ws.send(json.dumps({"method": "initialized", "params": {}}))

    # Get project dir
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", str(Path.cwd()))

    # Start thread
    ws.send(json.dumps({"id": 2, "method": "thread/start", "params": {
        "cwd": project_dir,
        "ephemeral": True,
        "sandbox": "read-only",
    }}))
    tr = json.loads(ws.recv())
    tid = tr.get("result", {}).get("thread", {}).get("id", "")
    if not tid:
        return None

    # Start turn
    ws.send(json.dumps({"id": 3, "method": "turn/start", "params": {
        "threadId": tid,
        "input": [{"type": "text", "text": prompt, "text_elements": []}],
    }}))

    # Wait for response - as long as Codex is active
    text = ""
    for _ in range(1000):
        if time.time() - t0 > MAX_TIMEOUT:
            break
        try:
            raw = ws.recv(timeout=INACTIVITY_TIMEOUT)
        except Exception:
            break
        msg = json.loads(raw)
        m = msg.get("method", "")
        if m == "turn/completed":
            break
        if m == "error":
            break
        if m == "item/completed":
            item = msg.get("params", {}).get("item", {})
            if item.get("type") == "agentMessage":
                t = item.get("text", "")
                if t:
                    text += t

    ws.close()
    return text.strip() if text.strip() else None


def ask_via_exec(prompt: str, strategic: bool = False) -> str | None:
    """Fallback: ask via codex exec (cold start).

    Delegates stdout parsing to ``parse_codex_exec_stdout`` which handles
    both v0.117 (sentinel-based) and v0.125 (header-on-stderr) formats.

    Args:
        prompt: The question/task to send to Codex.
        strategic: If True (Y27), use 900s (15 min) timeout for deep
            analyses (production-readiness reviews, architecture audits).
            Default False uses 180s (up from 120 to cover normal advisor
            consults that previously timed out silently).
    """
    timeout_s = 900 if strategic else 180
    logger.info(
        "ask_via_exec.enter prompt_len=%d strategic=%s timeout=%d",
        len(prompt or ""), strategic, timeout_s,
    )
    codex = shutil.which("codex")
    if not codex:
        logger.info("ask_via_exec.exit result_truthy=False reason=codex-not-in-path")
        return None
    try:
        r = subprocess.run(
            [codex, "exec", prompt[:3000], "-m", "gpt-5.5",
             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout_s,
        )
        if r.returncode != 0:
            logger.info("ask_via_exec.exit result_truthy=False reason=returncode-%d",
                        r.returncode)
            return None
        result = parse_codex_exec_stdout(r.stdout)
        logger.info("ask_via_exec.exit result_truthy=%s reason=ok", bool(result))
        return result
    except subprocess.TimeoutExpired:
        logger.exception("ask_via_exec.exit result_truthy=False reason=timeout")
        return None
    except Exception:
        logger.exception("ask_via_exec.exit result_truthy=False reason=exception")
        return None


def main():
    args = sys.argv[1:]
    strategic = False
    if "--strategic" in args:
        strategic = True
        args = [arg for arg in args if arg != "--strategic"]
    if not args:
        print("Usage: py -3 .claude/scripts/codex-ask.py [--strategic] \"your question\"",
              file=sys.stderr)
        sys.exit(1)

    prompt = " ".join(args)

    # Try broker first (fast, warm)
    result = None
    try:
        result = ask_via_broker(prompt)
    except Exception:
        pass

    # Fallback to codex exec
    if not result:
        result = ask_via_exec(prompt, strategic=strategic)

    if result:
        print(f"--- Codex gpt-5.5 opinion ---")
        print(result)
        print(f"---")
        # Mark as consulted for codex-gate.py
        _proj = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
        _ts = _proj / ".codex" / "last-consulted"
        _ts.parent.mkdir(parents=True, exist_ok=True)
        _ts.write_text(str(time.time()), encoding="utf-8")
        # Reset edit counter for codex-gate
        _ec = _proj / ".codex" / "edit-count"
        _ec.write_text("0", encoding="utf-8")
    else:
        print("Codex unavailable - proceed without second opinion.", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
