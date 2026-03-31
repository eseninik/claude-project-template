#!/usr/bin/env python3
# encoding: utf-8
"""PreToolUse hook: prevents agents from weakening linter/formatter configs.

Intercepts Edit and Write tool calls targeting linter/formatter config files.
If the change loosens rules (disabling, adding ignores, reducing strictness),
the hook blocks the operation (exit 2). Tightening or neutral changes pass through.

Exit codes:
  0 - allow (not a config file, or change is tightening/neutral)
  2 - block (change loosens linter/formatter rules)
"""

import json
import logging
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Windows encoding
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    for stream in [sys.stdin, sys.stdout, sys.stderr]:
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Logging (structured, to stderr)
# ---------------------------------------------------------------------------

logger = logging.getLogger("config-protection")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )

# ---------------------------------------------------------------------------
# Config file detection
# ---------------------------------------------------------------------------

CONFIG_BASENAME_PATTERNS = [
    # ESLint
    re.compile(r"^\.eslintrc(\.\w+)?$"),
    re.compile(r"^eslint\.config\.\w+$"),
    # Prettier
    re.compile(r"^\.prettierrc(\.\w+)?$"),
    re.compile(r"^prettier\.config\.\w+$"),
    # Python linters
    re.compile(r"^\.flake8$"),
    re.compile(r"^setup\.cfg$"),
    re.compile(r"^pyproject\.toml$"),
    # TypeScript
    re.compile(r"^tsconfig(\.\w+)?\.json$"),
    # Ruby
    re.compile(r"^\.rubocop\.ya?ml$"),
    # Go
    re.compile(r"^\.golangci\.ya?ml$"),
]


def is_config_file(file_path):
    """Check if the file path is a known linter/formatter config."""
    if not file_path:
        return False
    basename = Path(file_path).name
    for pat in CONFIG_BASENAME_PATTERNS:
        if pat.match(basename):
            return True
    return False


# ---------------------------------------------------------------------------
# Loosening detection patterns
# ---------------------------------------------------------------------------

_Q = "[\x27\x22]"  # single or double quote character class

LOOSENING_PATTERNS = [
    # ESLint: setting rules to "off"
    re.compile(_Q + r"off" + _Q, re.IGNORECASE),
    re.compile(r":\s*0\b"),
    # Inline suppression directives
    re.compile(r"noqa", re.IGNORECASE),
    re.compile(r"type:\s*ignore", re.IGNORECASE),
    re.compile(r"@ts-ignore", re.IGNORECASE),
    re.compile(r"@ts-nocheck", re.IGNORECASE),
    re.compile(r"#\s*nosec", re.IGNORECASE),
    re.compile(r"eslint-disable", re.IGNORECASE),
    re.compile(r"prettier-ignore", re.IGNORECASE),
    re.compile(r"rubocop:disable", re.IGNORECASE),
    re.compile(r"nolint", re.IGNORECASE),
    # TypeScript/tsconfig loosening
    re.compile(r'"strict"\s*:\s*false'),
    re.compile(r'"noImplicitAny"\s*:\s*false'),
    re.compile(r'"noImplicitReturns"\s*:\s*false'),
    re.compile(r'"noImplicitThis"\s*:\s*false'),
    re.compile(r'"strictNullChecks"\s*:\s*false'),
    re.compile(r'"strictFunctionTypes"\s*:\s*false'),
    re.compile(r'"strictBindCallApply"\s*:\s*false'),
    re.compile(r'"strictPropertyInitialization"\s*:\s*false'),
    re.compile(r'"noUnusedLocals"\s*:\s*false'),
    re.compile(r'"noUnusedParameters"\s*:\s*false'),
    re.compile(r'"noFallthroughCasesInSwitch"\s*:\s*false'),
    re.compile(r'"skipLibCheck"\s*:\s*true'),
    # Python: ruff/flake8/mypy loosening
    re.compile(r"extend-ignore", re.IGNORECASE),
    re.compile(r"per-file-ignores", re.IGNORECASE),
    re.compile(r"disable_error_code", re.IGNORECASE),
    re.compile(r"ignore_errors\s*=\s*[Tt]rue"),
    re.compile(r"disallow_untyped_defs\s*=\s*[Ff]alse"),
    re.compile(r"check_untyped_defs\s*=\s*[Ff]alse"),
    re.compile(r"warn_return_any\s*=\s*[Ff]alse"),
    re.compile(r"strict\s*=\s*[Ff]alse"),
    re.compile(r"select\s*=\s*\[\s*\]"),
    re.compile(r"disable\s*="),
    # Generic: bumping line length to unreasonable values
    re.compile(r"max-line-length\s*=\s*\d{3,}"),
    re.compile(r"max_line_length\s*=\s*\d{3,}"),
]

TIGHTENING_PATTERNS = [
    re.compile(_Q + r"error" + _Q, re.IGNORECASE),
    re.compile(r":\s*2\b"),
    re.compile(r'"strict"\s*:\s*true'),
    re.compile(r'"noImplicitAny"\s*:\s*true'),
    re.compile(r'"strictNullChecks"\s*:\s*true'),
    re.compile(r"disallow_untyped_defs\s*=\s*[Tt]rue"),
    re.compile(r"check_untyped_defs\s*=\s*[Tt]rue"),
    re.compile(r"strict\s*=\s*[Tt]rue"),
]

# For pyproject.toml / setup.cfg: only flag loosening in relevant sections
PYPROJECT_SECTION_PATTERNS = [
    re.compile(r"\[tool\.ruff"),
    re.compile(r"\[tool\.mypy"),
    re.compile(r"\[tool\.black"),
    re.compile(r"\[tool\.flake8"),
    re.compile(r"\[tool\.pylint"),
    re.compile(r"\[tool\.isort"),
    re.compile(r"tool\.ruff"),
    re.compile(r"tool\.mypy"),
    re.compile(r"tool\.black"),
    re.compile(r"tool\.flake8"),
    re.compile(r"tool\.pylint"),
    re.compile(r"tool\.isort"),
]

SETUPCFG_SECTION_PATTERNS = [
    re.compile(r"\[flake8\]"),
    re.compile(r"\[mypy"),
    re.compile(r"\[pylint"),
    re.compile(r"\[isort\]"),
]


def content_touches_linter_section(content, file_path):
    """For pyproject.toml and setup.cfg, check if content touches linter sections."""
    basename = Path(file_path).name.lower()
    if basename == "pyproject.toml":
        return any(p.search(content) for p in PYPROJECT_SECTION_PATTERNS)
    if basename == "setup.cfg":
        return any(p.search(content) for p in SETUPCFG_SECTION_PATTERNS)
    return True


def detect_loosening(text):
    """Return list of loosening signals found in text."""
    found = []
    for pat in LOOSENING_PATTERNS:
        matches = pat.findall(text)
        if matches:
            found.append("{} -> {}".format(pat.pattern, matches[:3]))
    return found


def detect_tightening(text):
    """Return list of tightening signals found in text."""
    found = []
    for pat in TIGHTENING_PATTERNS:
        if pat.search(text):
            found.append(pat.pattern)
    return found


def is_loosening_change(text, file_path):
    """Determine if the text content represents a loosening change.

    Returns (is_loosening, reasons).
    """
    if not content_touches_linter_section(text, file_path):
        logger.info("content does not touch linter sections, file=%s", file_path)
        return False, []

    loosening = detect_loosening(text)
    tightening = detect_tightening(text)

    if not loosening:
        return False, []

    # If tightening signals outnumber loosening, allow (net tightening)
    if tightening and len(tightening) >= len(loosening):
        logger.info(
            "tightening signals (%d) >= loosening signals (%d), allowing",
            len(tightening), len(loosening),
        )
        return False, []

    return True, loosening


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Hook profile gate
    try:
        from hook_base import should_run
        if not should_run("config-protection"):
            sys.exit(0)
    except ImportError:
        pass  # hook_base not available, continue

    logger.info("hook invoked")

    raw = sys.stdin.read()
    if not raw.strip():
        logger.info("empty stdin, allowing")
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("failed to parse stdin JSON: %s", exc)
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    logger.info("processing tool_name=%s", tool_name)

    if tool_name not in ("Edit", "Write"):
        logger.info("tool %s is not Edit/Write, allowing", tool_name)
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path:
        logger.info("no file_path in tool_input, allowing")
        sys.exit(0)

    if not is_config_file(file_path):
        logger.info("file %s is not a config file, allowing", file_path)
        sys.exit(0)

    logger.info("config file detected: %s", file_path)

    if tool_name == "Edit":
        new_string = tool_input.get("new_string", "")
        old_string = tool_input.get("old_string", "")
        # Check new_string for loosening patterns being ADDED
        text_to_check = new_string
        # Also detect deletion of tightening settings (BLOCKER fix from Codex review)
        # If old_string has strict settings being removed, that's loosening too
        if old_string and not new_string.strip():
            # Entire content being deleted — check if old had strictness
            text_to_check = ""  # will check old_string separately below
        deletion_loosening = False
        if old_string:
            old_tightening = detect_tightening(old_string)
            new_tightening = detect_tightening(new_string) if new_string else []
            if old_tightening and not new_tightening:
                deletion_loosening = True
                logger.info("deletion of tightening settings detected in old_string")
    elif tool_name == "Write":
        text_to_check = tool_input.get("content", "")
        old_string = ""
        deletion_loosening = False
        # For Write: compare new content with current on-disk file
        # to detect full-file rewrites that silently remove strict settings
        try:
            current_path = Path(file_path)
            if current_path.exists():
                current_content = current_path.read_text(encoding="utf-8", errors="ignore")
                old_tightening = detect_tightening(current_content)
                new_tightening = detect_tightening(text_to_check)
                if old_tightening and not new_tightening:
                    deletion_loosening = True
                    logger.info("Write removes tightening from existing file: %s", file_path)
        except Exception as e:
            logger.warning("could not read current file for comparison: %s", e)
    else:
        text_to_check = ""
        old_string = ""
        deletion_loosening = False

    if not text_to_check and not deletion_loosening:
        logger.info("no content to check and no deletion loosening, allowing")
        sys.exit(0)

    # Check for deletion-based loosening first
    if deletion_loosening:
        msg = "Config protection: removing strict settings weakens the linter. File: {}".format(file_path)
        logger.warning("BLOCKED deletion of tightening settings, file=%s", file_path)
        print(msg, file=sys.stderr)
        sys.exit(2)

    is_loose, reasons = is_loosening_change(text_to_check, file_path)

    if is_loose:
        msg = "Config protection: fix the code, do not weaken the linter. File: {}".format(file_path)
        logger.warning("BLOCKED loosening change, file=%s, reasons=%s", file_path, reasons[:5])
        print(msg, file=sys.stderr)
        sys.exit(2)

    logger.info("change is tightening or neutral, allowing. file=%s", file_path)
    sys.exit(0)


if __name__ == "__main__":
    main()
