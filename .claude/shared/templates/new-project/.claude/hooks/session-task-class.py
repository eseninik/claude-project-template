#!/usr/bin/env python3
"""Session Task Class Detector.

Runs on UserPromptSubmit. Reads the user's prompt, classifies it into one of:
  chat, typo, bugfix, feature, refactor, deploy

Writes the result to `.codex/task-class`. Other hooks (codex-watchdog) read
this file to decide how aggressive to be.

Classification is deterministic — regex + keyword rules. When nothing
matches, defaults to `feature` (medium strictness — errs toward caution).

Does NOT block anything. Silent on success.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    for _s in [sys.stdin, sys.stdout, sys.stderr]:
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger("session-task-class")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stderr,
)

DEFAULT_CLASS = "feature"
KNOWN_CLASSES = {"chat", "typo", "bugfix", "feature", "refactor", "deploy"}

# Ordered rules: first match wins. Each rule = (class, list of regex patterns).
# Patterns are case-insensitive. Russian + English.
RULES = [
    ("deploy", [
        r"\bdeploy\b", r"\bdeployment\b", r"в\s+прод", r"to\s+prod",
        r"\bproduction\b", r"systemctl", r"\brelease\b",
        r"задеплой", r"зарелизь", r"выкатить",
    ]),
    ("refactor", [
        r"\brefactor\w*\b", r"рефактор\w*", r"\bmigrate\b", r"\bmigration\b",
        r"\brewrite\b", r"переписать", r"переделать\s+весь",
    ]),
    ("bugfix", [
        r"\bfix\b", r"\bbug\b", r"\bbugfix\b", r"баг\b", r"починить",
        r"почини\b", r"исправь\b", r"исправь\s", r"ошибк\w*\s+в",
        r"\bfailing\b", r"не\s+работает", r"doesn.?t\s+work",
    ]),
    ("feature", [
        r"\bimplement\b", r"\badd\s+(a\s+)?new\b", r"\bcreate\s+(a\s+)?new\b",
        r"\bbuild\s+(a\s+)?new\b", r"добавь\b", r"создай\b", r"реализуй\b",
        r"сделай\s+(новый|новую|новое)", r"\bnew\s+feature\b",
        r"напиши\b",
    ]),
    ("typo", [
        r"\brename\b", r"переименуй\b", r"\btypo\b", r"опечатк",
        r"\brename\s+var", r"rename\s+this", r"переименуй\s+переменн",
    ]),
]


def get_project_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()


def classify(prompt: str) -> str:
    """Return one of KNOWN_CLASSES. Deterministic regex-based."""
    if not prompt or not prompt.strip():
        logger.info("classify result=chat reason=empty_prompt")
        return "chat"

    p = prompt.lower().strip()

    # Rules first — any pattern match wins, even on short prompts.
    for cls, patterns in RULES:
        for pat in patterns:
            if re.search(pat, p):
                logger.info("classify result=%s reason=pattern_match pattern=%s",
                            cls, pat)
                return cls

    # No rule matched — fall back to chat heuristic for short conversational.
    if len(p) < 80 and _looks_like_chat(p):
        logger.info("classify result=chat reason=short_conversational len=%d", len(p))
        return "chat"

    logger.info("classify result=%s reason=fallback_default len=%d",
                DEFAULT_CLASS, len(p))
    return DEFAULT_CLASS


def _looks_like_chat(p: str) -> bool:
    """Heuristic for short conversational messages.

    True if the prompt is short AND (ends with ?, is a greeting, OR lacks
    any file-ish / implementation-ish tokens).
    """
    chat_tokens = [
        "привет", "hello", "hi", "thanks", "спасибо", "да", "нет", "ok",
        "как дела", "что думаешь", "а что", "почему", "расскажи",
    ]
    impl_tokens = [
        "file", "файл", ".py", ".js", ".md", "class ", "def ", "function",
        "endpoint", "module", "модуль", "функци",
    ]

    if p.endswith("?"):
        return not any(t in p for t in impl_tokens)
    if any(t in p for t in chat_tokens):
        return True
    if not any(t in p for t in impl_tokens):
        return True
    return False


def write_class(project_dir: Path, cls: str) -> None:
    """Persist detected class to .codex/task-class atomically."""
    codex_dir = project_dir / ".codex"
    codex_dir.mkdir(parents=True, exist_ok=True)
    path = codex_dir / "task-class"
    tmp_path = path.with_suffix(f".tmp.{os.getpid()}")
    try:
        tmp_path.write_text(cls, encoding="utf-8")
        os.replace(tmp_path, path)
        logger.info("write_class path=%s value=%s", path, cls)
    except OSError as e:
        logger.warning("write_class fail=%s", e)
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass


def read_override(project_dir: Path) -> str | None:
    """Check if a user override is active (via /watchdog slash command)."""
    path = project_dir / ".codex" / "task-class-override"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("until", 0) > time.time():
            cls = data.get("class", "")
            if cls in KNOWN_CLASSES or cls == "off":
                logger.info("override_active class=%s until=%d", cls, data["until"])
                return cls
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("read_override fail=%s", e)
    return None


def main() -> None:
    # Hook profile gate (reuses hook_base; add to HOOK_PROFILES in hook_base.py)
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from hook_base import should_run
        if not should_run("session-task-class"):
            logger.info("main=skip reason=hook_profile")
            sys.exit(0)
    except ImportError:
        pass

    try:
        raw = sys.stdin.read()
        if not raw.strip():
            logger.info("main=skip reason=empty_stdin")
            sys.exit(0)
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as e:
        logger.info("main=skip reason=bad_stdin err=%s", e)
        sys.exit(0)

    prompt = ""
    if isinstance(payload, dict):
        prompt = (
            payload.get("prompt", "")
            or payload.get("user_prompt", "")
            or payload.get("content", "")
            or payload.get("message", "")
            or ""
        )

    project_dir = get_project_dir()

    # Honor override if active — keep it, skip classification
    override = read_override(project_dir)
    if override and override != "off":
        logger.info("main=keep_override class=%s", override)
        write_class(project_dir, override)
        sys.exit(0)

    cls = classify(prompt)
    write_class(project_dir, cls)
    sys.exit(0)


if __name__ == "__main__":
    main()
