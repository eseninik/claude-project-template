#!/usr/bin/env python3
"""Validate project configuration files against JSON schemas.

Checks:
  1. settings.json hooks section
  2. SKILL.md frontmatter (all skills)
  3. .mcp.json format

Usage:
    py -3 .claude/scripts/validate-configs.py [--verbose]

Exit codes:
    0 - all validations pass
    1 - one or more validations failed
"""

import json
import logging
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("validate-configs")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
CLAUDE_DIR = PROJECT_DIR / ".claude"
SCHEMAS_DIR = CLAUDE_DIR / "schemas"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"
SKILLS_DIR = CLAUDE_DIR / "skills"
MCP_FILE = PROJECT_DIR / ".mcp.json"

VERBOSE = "--verbose" in sys.argv

# ---------------------------------------------------------------------------
# Validation helpers (stdlib only, no jsonschema dependency)
# ---------------------------------------------------------------------------

VALID_HOOK_EVENTS = {
    "SessionStart", "PreToolUse", "PostToolUse", "PostToolUseFailure",
    "PreCompact", "TaskCompleted", "UserPromptSubmit", "Stop",
    "SessionEnd", "SubagentStart", "SubagentStop", "PermissionRequest",
    "WorktreeCreate", "WorktreeRemove",
}

results = []


def report(file: str, status: str, message: str = ""):
    """Record a validation result."""
    results.append({"file": file, "status": status, "message": message})
    icon = "PASS" if status == "PASS" else "FAIL"
    logger.info("file=%s status=%s %s", file, icon, message)
    if VERBOSE and message:
        print(f"  [{icon}] {file}: {message}", file=sys.stderr)


# ---------------------------------------------------------------------------
# 1. Validate settings.json hooks
# ---------------------------------------------------------------------------

def validate_hooks():
    """Validate hooks section of settings.json."""
    logger.info("action=validate_hooks.start file=%s", SETTINGS_FILE)

    if not SETTINGS_FILE.exists():
        report(str(SETTINGS_FILE), "FAIL", "File not found")
        return

    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        report(str(SETTINGS_FILE), "FAIL", f"Invalid JSON: {e}")
        return

    hooks = data.get("hooks", {})
    if not hooks:
        report(str(SETTINGS_FILE), "PASS", "No hooks section (valid)")
        return

    errors = []
    for event_name, event_hooks in hooks.items():
        if event_name not in VALID_HOOK_EVENTS:
            errors.append(f"Unknown hook event: {event_name}")
            continue

        if not isinstance(event_hooks, list):
            errors.append(f"{event_name}: must be an array")
            continue

        for i, entry in enumerate(event_hooks):
            hook_list = entry.get("hooks", [])
            if not hook_list:
                errors.append(f"{event_name}[{i}]: missing 'hooks' array")
                continue

            for j, hook in enumerate(hook_list):
                if "command" not in hook:
                    errors.append(f"{event_name}[{i}].hooks[{j}]: missing 'command'")
                if "type" not in hook:
                    errors.append(f"{event_name}[{i}].hooks[{j}]: missing 'type'")

                timeout = hook.get("timeout")
                if timeout is not None:
                    if not isinstance(timeout, int) or timeout < 1 or timeout > 300:
                        errors.append(f"{event_name}[{i}].hooks[{j}]: timeout must be 1-300")

    if errors:
        report(str(SETTINGS_FILE), "FAIL", "; ".join(errors))
    else:
        report(str(SETTINGS_FILE), "PASS", f"{len(hooks)} hook events configured")

    logger.info("action=validate_hooks.done errors=%d", len(errors))


# ---------------------------------------------------------------------------
# 2. Validate SKILL.md frontmatter
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def parse_yaml_simple(text: str) -> dict:
    """Simple YAML-like key-value parser for frontmatter.

    Handles basic scalars, arrays, and multiline values (> and |).
    """
    result = {}
    lines = text.strip().splitlines()
    current_key = None
    current_value_lines = []

    def flush():
        if current_key and current_value_lines:
            val = " ".join(current_value_lines).strip()
            if val.startswith("[") and val.endswith("]"):
                items = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
                result[current_key] = items
            else:
                result[current_key] = val.strip("'\"")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Check if line starts with a key (no leading whitespace in YAML top-level)
        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            flush()
            key, _, value = line.partition(":")
            current_key = key.strip()
            value = value.strip()
            if value in (">", "|", ">-", "|-"):
                current_value_lines = []  # multiline follows
            elif value:
                current_value_lines = [value]
            else:
                current_value_lines = []
        elif current_key:
            # continuation line (indented)
            current_value_lines.append(stripped)

    flush()
    return result


def validate_skills():
    """Validate all SKILL.md frontmatter."""
    logger.info("action=validate_skills.start dir=%s", SKILLS_DIR)

    if not SKILLS_DIR.exists():
        report(str(SKILLS_DIR), "FAIL", "Skills directory not found")
        return

    skill_count = 0
    error_count = 0

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        skill_count += 1
        content = skill_file.read_text(encoding="utf-8", errors="ignore")
        rel_path = str(skill_file.relative_to(PROJECT_DIR))

        match = FRONTMATTER_RE.match(content)
        if not match:
            report(rel_path, "FAIL", "Missing YAML frontmatter")
            error_count += 1
            continue

        fm = parse_yaml_simple(match.group(1))
        errors = []

        if "name" not in fm:
            errors.append("missing 'name'")
        elif not re.match(r"^[a-z0-9][a-z0-9-]*$", fm["name"]):
            errors.append(f"name '{fm['name']}' not kebab-case")

        if "description" not in fm:
            errors.append("missing 'description'")
        elif len(fm["description"]) < 20:
            errors.append("description too short (< 20 chars)")

        if errors:
            report(rel_path, "FAIL", "; ".join(errors))
            error_count += 1
        else:
            report(rel_path, "PASS", "")

    logger.info(
        "action=validate_skills.done total=%d errors=%d",
        skill_count, error_count,
    )


# ---------------------------------------------------------------------------
# 3. Validate .mcp.json
# ---------------------------------------------------------------------------

def validate_mcp():
    """Validate .mcp.json format."""
    logger.info("action=validate_mcp.start file=%s", MCP_FILE)

    if not MCP_FILE.exists():
        report(str(MCP_FILE), "PASS", "No .mcp.json (optional)")
        return

    try:
        data = json.loads(MCP_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        report(str(MCP_FILE), "FAIL", f"Invalid JSON: {e}")
        return

    servers = data.get("mcpServers", {})
    if not servers:
        report(str(MCP_FILE), "FAIL", "Empty mcpServers")
        return

    errors = []
    for name, config in servers.items():
        if "type" in config:
            if config["type"] in ("url", "sse"):
                if "url" not in config:
                    errors.append(f"{name}: type={config['type']} but missing 'url'")
            else:
                errors.append(f"{name}: unknown type '{config['type']}'")
        elif "command" in config:
            pass  # command-based server
        else:
            errors.append(f"{name}: must have 'type' or 'command'")

    if errors:
        report(str(MCP_FILE), "FAIL", "; ".join(errors))
    else:
        report(str(MCP_FILE), "PASS", f"{len(servers)} MCP servers configured")

    logger.info("action=validate_mcp.done errors=%d", len(errors))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    logger.info("action=validate.start project=%s", PROJECT_DIR)

    validate_hooks()
    validate_skills()
    validate_mcp()

    # Summary
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    print(f"\n{'=' * 50}", file=sys.stderr)
    print(f"  Validation: {passed} PASS, {failed} FAIL", file=sys.stderr)
    print(f"{'=' * 50}\n", file=sys.stderr)

    for r in results:
        if r["status"] == "FAIL":
            print(f"  FAIL: {r['file']}: {r['message']}", file=sys.stderr)

    logger.info("action=validate.done passed=%d failed=%d", passed, failed)

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
