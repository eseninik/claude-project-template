#!/usr/bin/env python3
"""
PostToolUse Write Validator Hook

Fires after every Write tool call. Validates .claude/skills/ and
.claude/memory/ markdown files for common issues:
  1. Empty file detection
  2. YAML frontmatter presence (skills only)
  3. Missing 'description' field in frontmatter (skills only)
  4. Merge conflict markers

Warn-don't-block: outputs warnings to stdout as JSON additionalContext.
Always exits 0.
"""

import json
import sys
from pathlib import Path


def main():
    # Hook profile check
    sys.path.insert(0, str(Path(__file__).parent))
    from hook_base import should_run
    if not should_run("write-validate"):
        sys.exit(0)

    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)
        cwd = Path(data.get("cwd", ".")).resolve()
        tool_input = data.get("tool_input", {})
        file_path_str = tool_input.get("file_path", "")

        if not file_path_str:
            sys.exit(0)

        file_path = Path(file_path_str).resolve()
        rel = file_path_str.replace("\\", "/")

        # Vaultguard: if CLAUDE.md doesn't exist in cwd, skip
        if not (cwd / "CLAUDE.md").exists():
            sys.exit(0)

        # Skip self: if path is inside .claude/hooks/
        if ".claude/hooks/" in rel:
            sys.exit(0)

        # Path filter: only validate .claude/skills/**/*.md and .claude/memory/**/*.md
        is_skill = ".claude/skills/" in rel and rel.endswith(".md")
        is_memory = ".claude/memory/" in rel and rel.endswith(".md")

        if not (is_skill or is_memory):
            sys.exit(0)

        filename = file_path.name
        warnings = []

        # Read the file content
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError):
            sys.exit(0)

        # Check 1: File not empty
        if file_path.stat().st_size == 0:
            warnings.append("Empty file written")

        # Check 2: YAML frontmatter (skills only)
        if is_skill and content.strip():
            if not content.startswith("---"):
                warnings.append("Missing YAML frontmatter")
            else:
                # Check for description field in first 20 lines
                head = content.splitlines()[:20]
                has_desc = any("description:" in line for line in head)
                if not has_desc:
                    warnings.append("Missing 'description' field")

        # Check 3: Merge conflict markers (constructed dynamically)
        marker_lt = "<" * 7
        marker_eq = "=" * 7
        marker_gt = ">" * 7
        for line in content.splitlines():
            if line.startswith(marker_lt) or line.startswith(marker_gt) or line.startswith(marker_eq):
                warnings.append("Merge conflict markers detected")
                break

        # Output warnings as JSON additionalContext
        if warnings:
            msg = f"Schema warnings for {filename}: " + ". ".join(warnings) + "."
            print(json.dumps({"additionalContext": msg}))

    except Exception as e:
        print(f"[write-validate] Error: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
