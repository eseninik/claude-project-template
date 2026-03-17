#!/usr/bin/env python3
"""
TruthGuard Mechanical Verification Hook (Python, stdlib only)

Ported from github.com/spyrae/truthguard bash scripts to Python.
Single file, 4 modes via CLI argument:

  py -3 .claude/hooks/truthguard.py pre-bash    # Block dangerous cmds + pre-commit tests
  py -3 .claude/hooks/truthguard.py pre-write   # Record file checksum before Write/Edit
  py -3 .claude/hooks/truthguard.py post-bash   # Verify exit codes, detect suppressed failures
  py -3 .claude/hooks/truthguard.py post-write  # Detect phantom edits (file unchanged)

Design principles:
  - Always exit 0 (never crash the hook pipeline)
  - stdlib only (no external deps)
  - Windows-native (no bash, no jq, no sha256sum)
  - Vaultguard: skip if no CLAUDE.md in cwd
"""

import json
import sys
import hashlib
import subprocess
import re
import os
from pathlib import Path
from datetime import datetime, timezone


# --- Storage ---
CHECKSUM_DIR = Path.home() / ".truthguard" / "checksums"
LOG_FILE = Path.home() / ".truthguard" / "session.log"


def log_event(msg: str):
    """Append to session log."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{ts} {msg}\n")
    except OSError:
        pass


def deny(reason: str):
    """PreToolUse: block the tool call."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }))
    sys.exit(0)


def ask(reason: str):
    """PreToolUse: ask user for confirmation."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason
        }
    }))
    sys.exit(0)


def add_context(msg: str):
    """PostToolUse: add context message (warn, don't block)."""
    print(json.dumps({"additionalContext": msg}))
    sys.exit(0)


def file_sha256(path: str) -> str:
    """Compute SHA256 of file content."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def path_key(path: str) -> str:
    """Encode file path as MD5 for checksum filename."""
    return hashlib.md5(path.encode("utf-8")).hexdigest()


# ================================================================
# MODE: pre-bash — Block dangerous commands + pre-commit test gate
# ================================================================

DANGEROUS_PATTERNS = [
    # DENY: git commit --no-verify
    (r'git\s+commit\b.*--no-verify', "deny",
     "Blocked git commit --no-verify. Skipping hooks defeats verification."),
    (r'git\s+commit\b.*\s-n\b', "deny",
     "Blocked git commit -n (--no-verify). Skipping hooks defeats verification."),

    # ASK: git push --force-with-lease (check BEFORE --force)
    (r'git\s+push\b.*force-with-lease', "ask",
     "git push --force-with-lease rewrites remote history. Are you sure?"),

    # DENY: git push --force / -f
    (r'git\s+push\b.*\s--force($|\s)', "deny",
     "Blocked git push --force. Use --force-with-lease for safer force push."),
    (r'git\s+push\b.*\s-f($|\s)', "deny",
     "Blocked git push -f. Use --force-with-lease for safer force push."),

    # ASK: git reset --hard
    (r'git\s+reset\s+--hard', "ask",
     "git reset --hard will discard all uncommitted changes. Are you sure?"),

    # ASK: git checkout -- (discard changes)
    (r'git\s+checkout\s+--\s', "ask",
     "git checkout -- will discard uncommitted changes to files. Are you sure?"),

    # ASK: git clean -f
    (r'git\s+clean\b.*-f', "ask",
     "git clean -f will permanently delete untracked files. Are you sure?"),

    # DENY: rm -rf on critical dirs (both flag orders: -rf and -fr)
    (r'rm\s+-\w*r\w*f\w*\s+(/($|\s)|~($|\s)|\$HOME($|\s)|\.git($|\s))', "deny",
     "Blocked rm -rf on critical directory."),
    (r'rm\s+-\w*f\w*r\w*\s+(/($|\s)|~($|\s)|\$HOME($|\s)|\.git($|\s))', "deny",
     "Blocked rm -rf on critical directory."),
]


def detect_test_command(cwd: str) -> str | None:
    """Auto-detect test framework from project files."""
    p = Path(cwd)

    if (p / "pubspec.yaml").exists():
        return "flutter test"
    if (p / "Cargo.toml").exists():
        return "cargo test"
    if (p / "go.mod").exists():
        return "go test ./..."
    if (p / "package.json").exists():
        try:
            pkg = json.loads((p / "package.json").read_text(encoding="utf-8"))
            test_script = pkg.get("scripts", {}).get("test", "")
            if test_script and 'echo "Error' not in test_script:
                return "npm test"
        except (json.JSONDecodeError, OSError):
            pass
    if (p / "pyproject.toml").exists() or (p / "pytest.ini").exists() or (p / "setup.cfg").exists():
        return "python -m pytest"
    if (p / "Makefile").exists():
        try:
            content = (p / "Makefile").read_text(encoding="utf-8", errors="ignore")
            if re.search(r'^test:', content, re.MULTILINE):
                return "make test"
        except OSError:
            pass

    return None


def pre_bash(data: dict):
    """PreToolUse Bash: block dangerous commands + pre-commit test gate."""
    cmd = data.get("tool_input", {}).get("command", "")
    cwd = data.get("cwd", ".")

    # --- Dangerous command checks ---
    for pattern, action, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd):
            log_event(f"{action} {cmd[:100]}")
            if action == "deny":
                deny(reason)
            else:
                ask(reason)

    # --- Pre-commit test gate ---
    if not re.search(r'git\s+commit\b', cmd):
        sys.exit(0)

    # Skip message-only amend
    if re.search(r'git\s+commit\s+--amend\s+(-m|--message)', cmd):
        sys.exit(0)

    test_cmd = detect_test_command(cwd)
    if not test_cmd:
        sys.exit(0)  # No tests found — allow commit

    try:
        result = subprocess.run(
            test_cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            output = result.stdout + result.stderr
            tail = "\n".join(output.splitlines()[-20:])
            log_event(f"commit-blocked exit={result.returncode} {test_cmd}")
            deny(
                f"Tests failed (exit {result.returncode}). Fix before committing.\n"
                f"Command: {test_cmd}\n\nOutput:\n{tail}"
            )
    except subprocess.TimeoutExpired:
        log_event(f"test-timeout {test_cmd}")
        deny(f"Tests timed out (120s). Command: {test_cmd}")
    except Exception as e:
        # Test runner failed to start — don't block, just log
        log_event(f"test-error {e}")


# ================================================================
# MODE: pre-write — Record file checksum before Write/Edit
# ================================================================

def pre_write(data: dict):
    """PreToolUse Write|Edit: save SHA256 of file before modification."""
    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path or not Path(file_path).exists():
        sys.exit(0)

    CHECKSUM_DIR.mkdir(parents=True, exist_ok=True)
    key = path_key(file_path)
    checksum = file_sha256(file_path)
    (CHECKSUM_DIR / key).write_text(checksum, encoding="utf-8")


# ================================================================
# MODE: post-bash — Verify exit codes, detect suppressed failures
# ================================================================

# Commands where non-zero exit is normal
EDGE_CASE_CMDS = [
    (r'(^|\||\s)(grep|rg|egrep|fgrep)\s', 1),
    (r'(^|\||\s)diff\s', 1),
    (r'(^|\s)(test|\[)\s', 1),
]

BUILD_FAIL_RE = re.compile(
    r'BUILD FAILED|build failed|compilation error|compile error|'
    r'SyntaxError|cannot find module|Module not found',
    re.IGNORECASE
)

TEST_FAIL_RE = re.compile(
    r'test.*FAILED|FAIL:|failures?:|errors? found|'
    r'AssertionError|assert.*failed|FAILURES!|'
    r'Tests:.*failed|failing test|pytest.*error',
    re.IGNORECASE
)


def post_bash(data: dict):
    """PostToolUse Bash: verify exit code, detect build/test failures."""
    cmd = data.get("tool_input", {}).get("command", "")
    resp = data.get("tool_response", {})
    exit_code = resp.get("exit_code", 0)

    if exit_code == 0:
        sys.exit(0)

    # Edge cases: non-zero is normal for these commands
    for pattern, expected_code in EDGE_CASE_CMDS:
        if re.search(pattern, cmd) and exit_code == expected_code:
            sys.exit(0)

    # Conditionals (||, &&, if) with non-fatal codes
    if re.search(r'\|\||&&|^\s*if\s', cmd):
        try:
            if int(exit_code) < 128:
                sys.exit(0)
        except (ValueError, TypeError):
            pass

    stdout = resp.get("stdout", "")
    stderr = resp.get("stderr", "")
    combined = f"{stdout}\n{stderr}"
    tail = "\n".join(combined.splitlines()[-15:])

    # Build failure — strong warning
    if BUILD_FAIL_RE.search(combined):
        log_event(f"build-fail exit={exit_code} {cmd[:100]}")
        add_context(
            f"Build failure detected (exit {exit_code}). "
            f"Fix errors before proceeding.\n\nOutput:\n{tail}"
        )

    # Test failure — strong warning
    if TEST_FAIL_RE.search(combined):
        log_event(f"test-fail exit={exit_code} {cmd[:100]}")
        add_context(
            f"Test failures detected (exit {exit_code}). "
            f"Fix before proceeding. Do NOT claim tests passed.\n\nOutput:\n{tail}"
        )

    # Generic non-zero — soft warning
    log_event(f"exit-code exit={exit_code} {cmd[:100]}")
    add_context(
        f"Command exited with code {exit_code}. "
        f"Verify actual result before claiming success.\n\nLast lines:\n{tail}"
    )


# ================================================================
# MODE: post-write — Detect phantom edits (file unchanged)
# ================================================================

def post_write(data: dict):
    """PostToolUse Write|Edit: compare pre/post checksums."""
    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path or not Path(file_path).exists():
        sys.exit(0)

    key = path_key(file_path)
    checksum_file = CHECKSUM_DIR / key

    if not checksum_file.exists():
        sys.exit(0)  # New file creation — no pre-checksum

    old_checksum = checksum_file.read_text(encoding="utf-8").strip()
    new_checksum = file_sha256(file_path)

    # Cleanup stored checksum
    try:
        checksum_file.unlink()
    except OSError:
        pass

    if old_checksum == new_checksum:
        basename = Path(file_path).name
        log_event(f"phantom-edit {file_path}")
        add_context(
            f"Phantom edit detected: '{basename}' was NOT actually modified "
            f"(checksum identical before and after). "
            f"Do NOT claim the file was updated."
        )


# ================================================================
# MAIN DISPATCHER
# ================================================================

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)

        # Vaultguard: skip if no CLAUDE.md in cwd
        cwd = Path(data.get("cwd", ".")).resolve()
        if not (cwd / "CLAUDE.md").exists():
            sys.exit(0)

        mode = sys.argv[1] if len(sys.argv) > 1 else ""

        if mode == "pre-bash":
            pre_bash(data)
        elif mode == "pre-write":
            pre_write(data)
        elif mode == "post-bash":
            post_bash(data)
        elif mode == "post-write":
            post_write(data)

    except Exception as e:
        print(f"[truthguard] Error: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
