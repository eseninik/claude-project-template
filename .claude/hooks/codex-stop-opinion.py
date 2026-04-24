#!/usr/bin/env python3
"""Stop hook: show Codex parallel opinion to user after Claude finishes.

This is the 100% reliable path — shows opinion via hook output,
not dependent on Claude choosing to display it.

Flow:
1. codex-parallel.py (UserPromptSubmit) launches Codex in background
2. Claude works and finishes
3. This Stop hook fires
4. Reads parallel-opinion.md
5. If fresh (<5 min): outputs formatted opinion
6. User sees it directly in terminal
"""

import json
import os
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    for s in [sys.stdin, sys.stdout, sys.stderr]:
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")

MAX_OPINION_AGE = 300  # 5 minutes
MAX_WAIT = 15  # max seconds to wait for Codex to finish
POLL_INTERVAL = 2  # check every 2 seconds


def main():
    try:
        raw = sys.stdin.read()
    except Exception:
        sys.exit(0)

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
    opinion_file = project_dir / ".codex" / "reviews" / "parallel-opinion.md"
    pid_file = project_dir / ".codex" / "parallel.pid"

    # If Codex is still running, wait briefly
    if pid_file.exists():
        waited = 0
        while pid_file.exists() and waited < MAX_WAIT:
            time.sleep(POLL_INTERVAL)
            waited += POLL_INTERVAL

    # Read opinion if fresh
    if not opinion_file.exists():
        sys.exit(0)

    try:
        age = time.time() - opinion_file.stat().st_mtime
        if age > MAX_OPINION_AGE:
            sys.exit(0)

        content = opinion_file.read_text(encoding="utf-8").strip()
        if not content or len(content) < 20:
            sys.exit(0)

        # Skip garbage responses
        skip_phrases = ["I need the actual", "I don't have", "No concrete user request", "no file or question"]
        if any(phrase in content for phrase in skip_phrases):
            sys.exit(0)

        # Output opinion via BOTH channels for maximum visibility:
        # 1. stdout JSON — Claude sees this as structured hook output
        opinion_block = f"--- Codex gpt-5.5 (parallel opinion) ---\n{content}\n---"
        output = {"additionalContext": opinion_block}
        print(json.dumps(output, ensure_ascii=False))
        # 2. stderr — shows directly in terminal
        print(f"\n{opinion_block}\n", file=sys.stderr)

    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
