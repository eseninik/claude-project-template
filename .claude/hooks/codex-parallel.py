#!/usr/bin/env python3
"""
Codex Parallel Advisor — runs on UserPromptSubmit hook.

Two jobs in one hook:
  1. INJECT previous Codex opinion via additionalContext (GUARANTEED delivery)
  2. LAUNCH new Codex for current request in background

Fixes applied (2026-03-30):
  - #1 (Claude): Wrapper params via JSON file, not f-string code injection
  - #2 (Claude): Race condition fixed — read opinion BEFORE clearing
  - #3 (Claude): Wrapper inherits UTF-8 encoding explicitly
  - #4 (Codex): PID kill validates process name before killing
  - #5 (Codex): get_project_context includes untracked files
  - #6 (Codex): Wrapper checks returncode, logs stderr, skips write on failure
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

logger = logging.getLogger("codex-parallel")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stderr,
)

if sys.platform == "win32":
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

MIN_PROMPT_LENGTH = 20
SKIP_PATTERNS = [
    "привет", "hello", "hi", "да", "нет", "yes", "no", "ок", "ok",
    "спасибо", "thanks", "продолжай", "continue", "давай", "go",
]
MAX_OPINION_AGE = 600  # 10 minutes


def find_codex():
    """Find codex binary."""
    codex_bin = shutil.which("codex")
    if codex_bin:
        return codex_bin
    npm_codex = Path.home() / "AppData" / "Roaming" / "npm" / "codex.cmd"
    if npm_codex.exists():
        return str(npm_codex)
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


def get_conversation_context(transcript_path, max_turns=3):
    """Read last N turns from transcript for conversation context."""
    if not transcript_path:
        return ""
    tp = Path(transcript_path)
    if not tp.exists():
        return ""
    try:
        size = tp.stat().st_size
        with open(tp, "r", encoding="utf-8", errors="replace") as f:
            if size > 10240:
                f.seek(size - 10240)
                f.readline()  # skip partial line
            lines = f.readlines()

        turns = []
        for line in reversed(lines):
            try:
                event = json.loads(line.strip())
                role = event.get("role", "")
                content = event.get("content", "")
                if role in ("user", "assistant") and content:
                    text = content[:300] if isinstance(content, str) else str(content)[:300]
                    turns.append(f"{role}: {text}")
                    if len(turns) >= max_turns:
                        break
            except (json.JSONDecodeError, TypeError):
                continue
        if turns:
            turns.reverse()
            return "Recent conversation:\n" + "\n".join(turns)
    except Exception:
        pass
    return ""


def get_project_context(project_dir):
    """Gather project context from multiple sources."""
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

    # FIX #5 (Codex): Include both tracked changes AND untracked files
    # FIX: fallback for fresh repos without HEAD
    changed = []
    for cmd in [["git", "diff", "--name-only", "HEAD"], ["git", "diff", "--name-only"]]:
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5, cwd=str(project_dir)
            )
            if result.stdout.strip():
                changed.extend(result.stdout.strip().splitlines()[:10])
                break
        except Exception:
            continue
    try:
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=5, cwd=str(project_dir)
        )
        if result.stdout.strip():
            changed.extend(result.stdout.strip().splitlines()[:5])
    except Exception:
        pass
    if changed:
        parts.append(f"Changed files: {', '.join(changed[:15])}")

    return "\n\n".join(parts)


def read_previous_opinion(project_dir):
    """Read previous Codex opinion if fresh enough."""
    opinion_file = project_dir / ".codex" / "reviews" / "parallel-opinion.md"
    if not opinion_file.exists():
        return None
    try:
        age = time.time() - opinion_file.stat().st_mtime
        if age > MAX_OPINION_AGE:
            return None
        content = opinion_file.read_text(encoding="utf-8").strip()
        if not content or "I need the actual" in content or "I don't have" in content:
            return None
        return content
    except Exception:
        return None


def safe_kill_previous(project_dir):
    """Kill previous Codex wrapper ONLY if PID belongs to our wrapper process."""
    pid_file = project_dir / ".codex" / "parallel.pid"
    if not pid_file.exists():
        return
    try:
        old_pid = int(pid_file.read_text().strip())
        if sys.platform == "win32":
            # Get full command line to verify it's OUR wrapper, not random python
            result = subprocess.run(
                ["wmic", "process", "where", f"ProcessId={old_pid}",
                 "get", "CommandLine", "/FORMAT:LIST"],
                capture_output=True, text=True, timeout=5
            )
            if "_parallel_wrapper" in result.stdout:
                subprocess.run(["taskkill", "/F", "/PID", str(old_pid)],
                               capture_output=True, timeout=5)
        else:
            cmdline_file = Path(f"/proc/{old_pid}/cmdline")
            if cmdline_file.exists():
                cmdline = cmdline_file.read_text(errors="replace")
                if "_parallel_wrapper" in cmdline:
                    os.kill(old_pid, 9)
        # Clean up stale PID file
        pid_file.unlink(missing_ok=True)
    except Exception:
        pass


def launch_codex_background(codex_bin, prompt_text, project_dir, transcript_path):
    """Launch Codex in background with rich context."""
    reviews_dir = project_dir / ".codex" / "reviews"
    opinion_file = reviews_dir / "parallel-opinion.md"
    reviews_dir.mkdir(parents=True, exist_ok=True)

    # FIX #4: Safe kill with PID validation
    safe_kill_previous(project_dir)

    # FIX #2 (Claude): Opinion already read by Job 1 in main().
    # Now safe to clear for new opinion.
    try:
        opinion_file.unlink(missing_ok=True)
    except Exception:
        pass

    # Gather context
    conversation = get_conversation_context(transcript_path)
    project = get_project_context(project_dir)

    # Adaptive reasoning effort
    low_words = prompt_text.lower()
    effort = "medium" if any(w in low_words for w in [
        "файл", "file", "код", "code", "review", "ревью",
        "анализ", "analyz", "debug", "баг", "bug", "фикс", "fix"
    ]) else "low"

    codex_prompt = (
        f"TASK: Answer the user request below. Give a direct, specific response in 3-6 lines. "
        f"Do NOT ask for more context. Do NOT say you need more information. "
        f"Work with what you have. If the request mentions files, read them.\n\n"
        f"User request: {prompt_text[:1000]}\n\n"
        f"{conversation}\n\n"
        f"Context: {project}"
    )

    # FIX #1 (Claude): Pass params via JSON file, not f-string code generation
    prompt_file = reviews_dir / "_prompt.txt"
    prompt_file.write_text(codex_prompt, encoding="utf-8")

    params_file = reviews_dir / "_params.json"
    params = {
        "codex_bin": codex_bin,
        "effort": effort,
        "project_dir": str(project_dir),
        "prompt_file": str(prompt_file),
        "opinion_file": str(opinion_file),
        "log_file": str(reviews_dir / "_wrapper.log"),
    }
    params_file.write_text(json.dumps(params, ensure_ascii=False), encoding="utf-8")

    # Wrapper script reads params from JSON — no code injection possible
    wrapper_file = reviews_dir / "_parallel_wrapper.py"
    wrapper_file.write_text(WRAPPER_SCRIPT, encoding="utf-8")

    try:
        process = subprocess.Popen(
            [sys.executable, str(wrapper_file), str(params_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(project_dir),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        pid_file = project_dir / ".codex" / "parallel.pid"
        pid_file.write_text(str(process.pid))
        logger.info("codex launched (PID %d), effort=%s", process.pid, effort)
    except Exception as e:
        logger.error("failed to launch codex: %s", e)


# FIX #1 (Claude): Static wrapper script — no dynamic code generation
# FIX #3 (Claude): Explicit UTF-8 encoding setup
# FIX #6 (Codex): Error handling — check returncode, log stderr, skip on failure
WRAPPER_SCRIPT = r'''#!/usr/bin/env python3
"""Codex wrapper — launched in background by codex-parallel.py
Uses -o flag to write FULL output to file (no 200-line truncation).
Retries once on model refresh timeout (intermittent network issue).
"""
import json, subprocess, sys, pathlib, time

if sys.platform == "win32":
    for s in [sys.stdin, sys.stdout, sys.stderr]:
        s.reconfigure(encoding="utf-8", errors="replace")

params_path = pathlib.Path(sys.argv[1])
params = json.loads(params_path.read_text(encoding="utf-8"))

prompt = pathlib.Path(params["prompt_file"]).read_text(encoding="utf-8")
opinion_path = pathlib.Path(params["opinion_file"])
log_path = pathlib.Path(params["log_file"])

args = [
    params["codex_bin"], "exec", "-",
    "-m", "gpt-5.5",
    "-c", f"reasoning.effort={params['effort']}",
    "--sandbox", "read-only",
    "--full-auto", "--ephemeral",
    "-o", str(opinion_path),
]

MAX_RETRIES = 2
RETRY_DELAY = 5

def run_codex():
    return subprocess.run(
        args, input=prompt,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
        timeout=180, cwd=params["project_dir"],
    )

try:
    last_err = ""
    for attempt in range(MAX_RETRIES):
        result = run_codex()
        if result.returncode == 0:
            break
        last_err = result.stderr[:500]
        # Retry on model refresh timeout (intermittent network issue)
        if "timeout" in last_err.lower() and "model" in last_err.lower() and attempt < MAX_RETRIES - 1:
            log_path.write_text(
                f"Codex model refresh timeout, retrying in {RETRY_DELAY}s (attempt {attempt + 1}/{MAX_RETRIES})",
                encoding="utf-8",
            )
            try: opinion_path.unlink(missing_ok=True)
            except: pass
            time.sleep(RETRY_DELAY)
            continue
        # Non-retryable failure
        log_path.write_text(
            f"Codex failed (exit {result.returncode})\nstderr: {last_err}",
            encoding="utf-8",
        )
        try: opinion_path.unlink(missing_ok=True)
        except: pass
        sys.exit(1)

    # Verify opinion file was written and has content
    if not opinion_path.exists() or opinion_path.stat().st_size < 10:
        log_path.write_text(
            f"Codex produced empty output. stderr: {result.stderr[:500]}",
            encoding="utf-8",
        )

except subprocess.TimeoutExpired:
    log_path.write_text("Codex timed out after 180s", encoding="utf-8")
except Exception as e:
    log_path.write_text(f"Wrapper error: {e}", encoding="utf-8")
finally:
    pid_path = pathlib.Path(params["project_dir"]) / ".codex" / "parallel.pid"
    try: pid_path.unlink(missing_ok=True)
    except: pass
'''


def main():
    # Hook profile gate
    try:
        from hook_base import should_run
        if not should_run("codex-parallel"):
            sys.exit(0)
    except ImportError:
        pass

    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        payload = json.loads(raw)

        # Extract fields
        prompt_text = ""
        transcript_path = ""
        if isinstance(payload, dict):
            prompt_text = (
                payload.get("prompt", "")
                or payload.get("message", "")
                or payload.get("content", "")
                or payload.get("input", "")
                or ""
            )
            transcript_path = payload.get("transcript_path", "")
        elif isinstance(payload, str):
            prompt_text = payload

        project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()

        # === JOB 1: Inject PREVIOUS Codex opinion via additionalContext ===
        previous_opinion = read_previous_opinion(project_dir)

        # === JOB 2: Launch NEW Codex for current request ===
        if prompt_text and not should_skip(prompt_text):
            codex_bin = find_codex()
            if codex_bin:
                launch_codex_background(codex_bin, prompt_text, project_dir, transcript_path)

        # === Inject opinion if available ===
        if previous_opinion:
            output = {
                "additionalContext": (
                    f"--- Codex gpt-5.5 (parallel advisor) ---\n"
                    f"{previous_opinion}\n"
                    f"--- end Codex opinion ---\n"
                    f"Consider this Codex opinion in your response. "
                    f"Mention agreements and disagreements with Codex."
                )
            }
            print(json.dumps(output, ensure_ascii=False))
            logger.info("injected codex opinion (%d chars)", len(previous_opinion))

    except Exception as e:
        logger.error("unexpected error: %s", e)

    sys.exit(0)


if __name__ == "__main__":
    main()
