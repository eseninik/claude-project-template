#!/usr/bin/env python3
"""Codex Warm Broker — persistent Codex app-server with WebSocket communication.

Replaces codex-parallel.py + codex-stop-opinion.py with a single reliable system.

Architecture:
  SessionStart  → starts 'codex app-server --listen ws://127.0.0.1:{PORT}'
  UserPromptSubmit → connects via WebSocket, sends prompt, gets opinion in 0.5-2 sec
  Stop → reads opinion file, shows to user via stderr + additionalContext
  SessionEnd → kills broker process

The broker stays warm for the entire CC session — no cold start per request.
"""

import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Windows encoding
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    for s in [sys.stdin, sys.stdout, sys.stderr]:
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("codex-broker")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stderr,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BROKER_PORT = 4500
BROKER_URL = f"ws://127.0.0.1:{BROKER_PORT}"
MAX_OPINION_AGE = 300  # 5 minutes
OPINION_TIMEOUT = 20  # seconds to wait for opinion in Stop hook
MIN_PROMPT_LENGTH = 20
SKIP_PATTERNS = [
    "привет", "hello", "hi", "да", "нет", "yes", "no", "ок", "ok",
    "спасибо", "thanks", "продолжай", "continue", "давай", "go",
]


def get_project_dir():
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()


def get_state_dir(project_dir):
    """Get .codex/ directory for this project."""
    d = project_dir / ".codex"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_broker_pid_file(project_dir):
    return get_state_dir(project_dir) / "broker.pid"


def get_opinion_file(project_dir):
    return get_state_dir(project_dir) / "reviews" / "parallel-opinion.md"


def get_reviews_dir(project_dir):
    d = project_dir / ".codex" / "reviews"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Broker lifecycle
# ---------------------------------------------------------------------------

def is_broker_running(project_dir):
    """Check if broker process is alive."""
    pid_file = get_broker_pid_file(project_dir)
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        # Check if process exists
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=3
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        return False


def start_broker(project_dir):
    """Start codex app-server as background process."""
    codex_bin = shutil.which("codex")
    if not codex_bin:
        npm_codex = Path.home() / "AppData" / "Roaming" / "npm" / "codex.cmd"
        if npm_codex.exists():
            codex_bin = str(npm_codex)
        else:
            logger.warning("codex not found, cannot start broker")
            return False

    pid_file = get_broker_pid_file(project_dir)
    log_file = get_state_dir(project_dir) / "broker.log"

    # Kill old broker if exists
    if is_broker_running(project_dir):
        stop_broker(project_dir)

    args = [
        codex_bin, "app-server",
        "--listen", BROKER_URL,
        "-c", "model=gpt-5.4",
    ]

    logger.info("starting broker: %s", " ".join(args[:5]))

    try:
        log_fh = open(str(log_file), "w", encoding="utf-8")
        process = subprocess.Popen(
            args,
            stdout=log_fh,
            stderr=log_fh,
            cwd=str(project_dir),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        pid_file.write_text(str(process.pid))
        logger.info("broker started (PID %d) on %s", process.pid, BROKER_URL)

        # Wait for broker to be ready
        time.sleep(2)
        if process.poll() is not None:
            logger.error("broker died immediately, exit code: %s", process.returncode)
            log_content = log_file.read_text(encoding="utf-8", errors="replace")[:500]
            logger.error("broker log: %s", log_content)
            return False

        return True
    except Exception as e:
        logger.error("failed to start broker: %s", e)
        return False


def stop_broker(project_dir):
    """Stop the broker process."""
    pid_file = get_broker_pid_file(project_dir)
    if not pid_file.exists():
        return

    try:
        pid = int(pid_file.read_text().strip())
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(pid)],
                capture_output=True, timeout=5
            )
        else:
            os.kill(pid, signal.SIGTERM)
        logger.info("broker stopped (PID %d)", pid)
    except Exception as e:
        logger.warning("failed to stop broker: %s", e)
    finally:
        try:
            pid_file.unlink(missing_ok=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# WebSocket communication
# ---------------------------------------------------------------------------

def send_prompt_to_broker(project_dir, prompt_text):
    """Send prompt to warm broker via WebSocket background subprocess."""
    opinion_file = get_opinion_file(project_dir)
    reviews_dir = get_reviews_dir(project_dir)
    log_file = reviews_dir / "_wrapper.log"

    # Clear old opinion
    try:
        opinion_file.unlink(missing_ok=True)
    except Exception:
        pass

    # Build context
    context = get_project_context(project_dir)
    full_prompt = (
        f"You are a parallel code advisor. Another AI (Claude) is working on this task. "
        f"Give your independent opinion in 3-6 lines. Be specific, mention file names. "
        f"Focus on bugs, security issues, edge cases the other AI might miss.\n\n"
        f"User request: {prompt_text[:1000]}\n\n"
        f"Context: {context}"
    )

    # Write prompt and params for external WS client
    prompt_file = reviews_dir / "_prompt.txt"
    prompt_file.write_text(full_prompt, encoding="utf-8")

    params = {
        "broker_url": BROKER_URL,
        "project_dir": str(project_dir),
        "prompt_file": str(prompt_file),
        "opinion_file": str(opinion_file),
        "log_file": str(log_file),
    }
    params_file = reviews_dir / "_params.json"
    params_file.write_text(json.dumps(params), encoding="utf-8")

    # Use standalone _ws_client.py (not f-string generated)
    # Copy from template if not exists in project
    ws_client_src = Path(__file__).resolve().parent.parent.parent / ".codex" / "reviews" / "_ws_client.py"
    ws_client_dst = reviews_dir / "_ws_client.py"
    if ws_client_src.exists() and ws_client_src != ws_client_dst:
        import shutil as _shutil
        _shutil.copy2(str(ws_client_src), str(ws_client_dst))
    elif not ws_client_dst.exists():
        # Minimal fallback — should not happen if deployed correctly
        logger.error("_ws_client.py not found at %s", ws_client_dst)
        return False

    try:
        process = subprocess.Popen(
            [sys.executable, str(ws_client_dst), str(params_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(project_dir),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        (reviews_dir / "_ws_client.pid").write_text(str(process.pid))
        logger.info("ws client launched (PID %d)", process.pid)
        return True
    except Exception as e:
        logger.error("failed to launch ws client: %s", e)
        return False


def get_project_context(project_dir):
    """Gather project context."""
    parts = []
    claude_md = project_dir / "CLAUDE.md"
    if claude_md.exists():
        try:
            parts.append(f"Project: {claude_md.read_text(encoding='utf-8')[:300].strip()}")
        except Exception:
            pass

    ctx_file = project_dir / ".claude" / "memory" / "activeContext.md"
    if ctx_file.exists():
        try:
            content = ctx_file.read_text(encoding="utf-8")
            if "## Current Focus" in content:
                parts.append(f"Current work:\n{content.split('## Current Focus')[1][:600].strip()}")
        except Exception:
            pass

    # Changed files
    changed = []
    for cmd in [["git", "diff", "--name-only", "HEAD"], ["git", "diff", "--name-only"]]:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=5, cwd=str(project_dir))
            if r.stdout.strip():
                changed.extend(r.stdout.strip().splitlines()[:10])
                break
        except Exception:
            continue
    if changed:
        parts.append(f"Changed files: {', '.join(changed[:15])}")

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Opinion display
# ---------------------------------------------------------------------------

def get_codex_opinion_sync(project_dir, prompt_text, max_timeout=300):
    """Call Codex broker SYNCHRONOUSLY and return opinion text.

    Waits AS LONG AS Codex is actively working (receiving notifications).
    Only gives up if:
    - Codex returns turn/completed (normal finish)
    - Codex returns error (broken)
    - No message received for 30 seconds (stalled/dead)
    - Absolute max 5 minutes (safety net)

    Claude does NOT start until this returns.
    """
    context = get_project_context(project_dir)
    full_prompt = (
        f"You are a parallel code advisor. Another AI (Claude) is about to work on this task. "
        f"Give your independent opinion in 3-6 lines BEFORE Claude starts. "
        f"Focus on: approach suggestions, potential pitfalls, files to check, edge cases.\n\n"
        f"User request: {prompt_text[:1000]}\n\n"
        f"Context: {context}"
    )

    try:
        from websockets.sync.client import connect

        t0 = time.time()
        ws = connect(BROKER_URL, close_timeout=3, open_timeout=3)

        # Initialize
        ws.send(json.dumps({"id": 1, "method": "initialize", "params": {
            "clientInfo": {"title": "Codex Parallel", "name": "codex-parallel", "version": "1.0.0"},
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

        # Start thread
        ws.send(json.dumps({"id": 2, "method": "thread/start", "params": {
            "cwd": str(project_dir),
            "ephemeral": True,
            "sandbox": "read-only",
        }}))
        tr = json.loads(ws.recv())
        tid = tr.get("result", {}).get("thread", {}).get("id", "")
        if not tid:
            logger.warning("no thread id from broker")
            ws.close()
            return None

        # Start turn
        ws.send(json.dumps({"id": 3, "method": "turn/start", "params": {
            "threadId": tid,
            "input": [{"type": "text", "text": full_prompt, "text_elements": []}],
        }}))

        # Wait for response — as long as Codex is alive and working
        # 30s inactivity timeout (no messages = Codex stalled)
        # 300s absolute max (safety net)
        INACTIVITY_TIMEOUT = 30
        text = ""
        for _ in range(1000):
            elapsed = time.time() - t0
            if elapsed > max_timeout:
                logger.warning("absolute timeout %ds reached", max_timeout)
                break
            try:
                raw = ws.recv(timeout=INACTIVITY_TIMEOUT)
            except Exception:
                logger.warning("no message for %ds — Codex stalled, proceeding without", INACTIVITY_TIMEOUT)
                break
            msg = json.loads(raw)
            m = msg.get("method", "")
            if m == "turn/completed":
                logger.info("turn completed normally")
                break
            if m == "error":
                logger.warning("codex error: %s", json.dumps(msg)[:200])
                break
            if m == "item/completed":
                item = msg.get("params", {}).get("item", {})
                if item.get("type") == "agentMessage":
                    t = item.get("text", "")
                    if t:
                        text += t

        ws.close()
        elapsed = time.time() - t0
        logger.info("codex sync response: %d chars in %.1fs", len(text), elapsed)

        if text.strip() and len(text.strip()) > 15:
            # Also save to file for reference
            opinion_file = get_opinion_file(project_dir)
            get_reviews_dir(project_dir)
            opinion_file.write_text(text.strip(), encoding="utf-8")
            return text.strip()
        return None

    except ImportError:
        logger.warning("websockets not installed")
        return None
    except Exception as e:
        logger.warning("sync codex failed: %s", e)
        return None


def read_opinion(project_dir, max_wait=0):
    """Read opinion file, optionally waiting for it."""
    opinion_file = get_opinion_file(project_dir)
    ws_pid_file = get_reviews_dir(project_dir) / "_ws_client.pid"

    # Wait for ws client to finish if still running
    waited = 0
    while max_wait > 0 and waited < max_wait:
        if opinion_file.exists() and opinion_file.stat().st_size > 20:
            break
        if not ws_pid_file.exists():
            break  # Client finished, no opinion
        time.sleep(1)
        waited += 1

    if not opinion_file.exists():
        return None

    try:
        age = time.time() - opinion_file.stat().st_mtime
        if age > MAX_OPINION_AGE:
            return None

        content = opinion_file.read_text(encoding="utf-8").strip()
        if not content or len(content) < 20:
            return None

        # Filter garbage
        skip = ["I need the actual", "I don't have", "No concrete user request",
                "no file or question", "no actual user request", "target request is missing"]
        if any(phrase.lower() in content.lower() for phrase in skip):
            return None

        return content
    except Exception:
        return None


def should_skip(prompt_text):
    """Skip trivial messages."""
    text = prompt_text.strip().lower()
    if len(text) < MIN_PROMPT_LENGTH:
        return True
    for p in SKIP_PATTERNS:
        if text == p or text.startswith(f"{p} ") or text.startswith(f"{p},"):
            return True
    if text.startswith("/"):
        return True
    return False


# ---------------------------------------------------------------------------
# Hook handlers
# ---------------------------------------------------------------------------

def handle_session_start(payload):
    """Start broker at session beginning."""
    project_dir = get_project_dir()
    if not is_broker_running(project_dir):
        start_broker(project_dir)
    else:
        logger.info("broker already running")


def handle_user_prompt(payload):
    """Get Codex opinion SYNCHRONOUSLY before Claude starts working.

    Flow:
    1. Send user prompt to warm Codex broker
    2. WAIT for response (up to 18 sec)
    3. Inject Codex opinion into Claude's context via additionalContext
    4. Claude starts working WITH Codex opinion already available
    """
    project_dir = get_project_dir()

    # Extract prompt
    prompt_text = ""
    if isinstance(payload, dict):
        prompt_text = (
            payload.get("prompt", "")
            or payload.get("message", "")
            or payload.get("content", "")
            or payload.get("input", "")
            or ""
        )

    if not prompt_text or should_skip(prompt_text):
        logger.info("skipped: prompt too short or trivial")
        return

    # SYNCHRONOUS: get Codex opinion NOW, before Claude starts
    opinion = get_codex_opinion_sync(project_dir, prompt_text)

    if opinion:
        output = {
            "additionalContext": (
                f"--- Codex gpt-5.4 (parallel advisor — BEFORE your work) ---\n"
                f"{opinion}\n"
                f"--- end Codex opinion ---\n"
                f"IMPORTANT: Consider this Codex opinion BEFORE you start working. "
                f"Adjust your approach based on Codex's suggestions. "
                f"Mention in your response if you agree or disagree with Codex."
            )
        }
        print(json.dumps(output, ensure_ascii=False))
        logger.info("injected SYNC opinion (%d chars)", len(opinion))
    else:
        logger.info("no opinion received within timeout")


def handle_stop(payload):
    """Show Codex opinion after Claude finishes."""
    project_dir = get_project_dir()
    opinion = read_opinion(project_dir, max_wait=OPINION_TIMEOUT)

    if opinion:
        block = f"--- Codex gpt-5.4 (parallel opinion) ---\n{opinion}\n---"
        # systemMessage — shown DIRECTLY to user in terminal (100% visible)
        output = {"systemMessage": block}
        print(json.dumps(output, ensure_ascii=False))
        logger.info("displayed opinion via systemMessage (%d chars)", len(opinion))


def handle_session_end(payload):
    """Stop broker when session ends."""
    project_dir = get_project_dir()
    stop_broker(project_dir)


# ---------------------------------------------------------------------------
# Main — routes based on hook event
# ---------------------------------------------------------------------------

def main():
    # Hook profile gate
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from hook_base import should_run
        if not should_run("codex-broker"):
            sys.exit(0)
    except ImportError:
        pass

    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, Exception):
        payload = {}

    # Detect which hook event called us
    hook_event = os.environ.get("CLAUDE_HOOK_EVENT", "")

    if not hook_event:
        # Fallback: detect from payload or argv
        if len(sys.argv) > 1:
            hook_event = sys.argv[1]

    if hook_event == "SessionStart":
        handle_session_start(payload)
    elif hook_event == "UserPromptSubmit":
        handle_user_prompt(payload)
    elif hook_event == "Stop":
        handle_stop(payload)
    elif hook_event == "SessionEnd":
        handle_session_end(payload)
    else:
        # Auto-detect: if payload has "prompt", it's UserPromptSubmit
        if isinstance(payload, dict) and payload.get("prompt"):
            handle_user_prompt(payload)
        else:
            logger.info("unknown event, payload keys: %s", list(payload.keys()) if isinstance(payload, dict) else "N/A")

    sys.exit(0)


if __name__ == "__main__":
    main()
