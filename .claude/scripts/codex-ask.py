#!/usr/bin/env python3
"""Codex Ask — CLI tool for Claude to get Codex opinion on any task.

Usage:
    py -3 .claude/scripts/codex-ask.py "Your question or task description"

Connects to warm Codex broker (ws://127.0.0.1:4500), sends question,
waits for response, prints to stdout. Claude reads the output.

Works everywhere: main session, subtasks, Agent Teams, pipeline phases.
If broker is not running, falls back to codex exec.
"""

import json
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

    # Wait for response — as long as Codex is active
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


def ask_via_exec(prompt):
    """Fallback: ask via codex exec (cold start)."""
    codex = shutil.which("codex")
    if not codex:
        return None
    try:
        r = subprocess.run(
            [codex, "exec", prompt[:3000], "-m", "gpt-5.4",
             "--sandbox", "read-only", "--full-auto", "--ephemeral"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120,
        )
        if r.returncode == 0:
            lines = r.stdout.strip().splitlines()
            content = []
            in_resp = False
            for line in lines:
                if line.strip() == "codex" and not in_resp:
                    in_resp = True
                    continue
                if in_resp and "tokens used" in line:
                    break
                if in_resp:
                    content.append(line)
            return "\n".join(content).strip() or None
    except Exception:
        pass
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: py -3 .claude/scripts/codex-ask.py \"your question\"", file=sys.stderr)
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    # Try broker first (fast, warm)
    result = None
    try:
        result = ask_via_broker(prompt)
    except Exception:
        pass

    # Fallback to codex exec
    if not result:
        result = ask_via_exec(prompt)

    if result:
        print(f"--- Codex gpt-5.4 opinion ---")
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
        print("Codex unavailable — proceed without second opinion.", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
