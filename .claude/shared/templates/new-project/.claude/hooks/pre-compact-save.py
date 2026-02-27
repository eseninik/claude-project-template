#!/usr/bin/env python3
"""
PreCompact Memory Save Hook

Reads the session transcript (JSONL), extracts key information via OpenRouter Haiku,
and saves to daily/ log + activeContext.md before compaction wipes the context.

Replicates OpenClaw's "silent turn" pre-compaction memory flush,
but as a Claude Code hook instead of embedded runtime code.

IMPORTANT: This script must NEVER block compaction. All errors -> exit 0.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# --- Configuration ---
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-haiku-4.5"
MAX_TRANSCRIPT_MESSAGES = 50
MAX_TRANSCRIPT_CHARS = 8000
API_TIMEOUT_SECONDS = 30
MAX_TOKENS = 600

# --- Curation ---
ACTIVE_CONTEXT_MAX_LINES = 150
DEDUP_WINDOW_MINUTES = 5
MAX_PRECOMPACT_NOTES = 3

EXTRACTION_PROMPT = """You are a memory extraction agent for a development session.
From this conversation transcript, extract the most important information.

Output in this EXACT format (no extra text before or after):

**Did:** [1-2 sentences: what was accomplished]
**Decided:** [key decisions made, or "none"]
**Learned:** [new insights, patterns, gotchas discovered, or "none"]
**Next:** [what should happen next session]
**Patterns:** [any new reusable patterns, or "none"]
**Gotchas:** [any new pitfalls discovered, or "none"]

Be concise. Focus on WHAT changed and WHY, not step-by-step details."""


def find_api_key(cwd: Path) -> str | None:
    """Find OpenRouter API key from multiple sources."""
    # 1. Environment variable
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key

    # 2. Project .claude/hooks/.env
    env_file = cwd / ".claude" / "hooks" / ".env"
    key = _read_key_from_env(env_file, "OPENROUTER_API_KEY")
    if key:
        return key

    # 3. Graphiti docker .env (fallback — uses OPENAI_API_KEY for OpenRouter)
    home = Path.home()
    graphiti_env = home / "graphiti" / "mcp_server" / "docker" / ".env"
    key = _read_key_from_env(graphiti_env, "OPENAI_API_KEY")
    if key and key.startswith("sk-or-"):
        return key

    return None


def _read_key_from_env(path: Path, key_name: str) -> str | None:
    """Read a key=value from a .env file."""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{key_name}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except (FileNotFoundError, PermissionError, OSError):
        pass
    return None


def find_transcript(hook_input: dict) -> Path | None:
    """Find the JSONL transcript file. Handles empty transcript_path bug (#13668)."""
    transcript_path = hook_input.get("transcript_path", "")

    if transcript_path and Path(transcript_path).exists():
        return Path(transcript_path)

    # Fallback: find latest .jsonl by session_id or modification time
    session_id = hook_input.get("session_id", "")
    cwd = hook_input.get("cwd", ".")

    # Claude stores transcripts in ~/.claude/projects/{project-slug}/
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return None

    # Try to find by session_id first
    if session_id:
        for proj_dir in projects_dir.iterdir():
            if proj_dir.is_dir():
                jsonl = proj_dir / f"{session_id}.jsonl"
                if jsonl.exists():
                    return jsonl

    # Fallback: find the project dir matching cwd, then latest .jsonl by mtime
    cwd_slug = Path(cwd).resolve().as_posix().replace("/", "-").replace(":", "-").lstrip("-")
    # Try common slug patterns
    for proj_dir in projects_dir.iterdir():
        if not proj_dir.is_dir():
            continue
        # Match by slug similarity (Claude uses drive-letter--path format)
        proj_name = proj_dir.name
        if _paths_match(proj_name, cwd):
            jsonls = sorted(proj_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
            if jsonls:
                return jsonls[0]

    return None


def _paths_match(slug: str, cwd: str) -> bool:
    """Check if a project slug matches the working directory."""
    # Claude Code slug format: C--Users-name-project -> C:/Users/name/project
    cwd_parts = Path(cwd).resolve().parts
    slug_lower = slug.lower().replace("-", "")
    cwd_joined = "".join(p.lower().replace("\\", "").replace("/", "").replace(":", "") for p in cwd_parts)
    # Fuzzy match: check if significant parts overlap
    return len(cwd_joined) > 5 and (cwd_joined in slug_lower or slug_lower in cwd_joined)


def read_transcript(path: Path) -> str:
    """Read and filter transcript messages, returning a condensed text."""
    messages = []
    total_chars = 0

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, PermissionError, OSError):
        return ""

    # Read from the END (most recent messages are most important)
    for line in reversed(lines):
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_type = data.get("type", "")
        message = data.get("message", {})
        if not isinstance(message, dict):
            continue

        role = message.get("role", "")
        content = message.get("content", "")

        # Extract text content
        text = ""
        if msg_type == "user" and role == "user" and isinstance(content, str):
            # Skip tool results embedded as user messages
            if not content.startswith('{"type":"tool_result"'):
                text = f"User: {content}"
        elif msg_type == "assistant" and role == "assistant":
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = f"Assistant: {block.get('text', '')}"
                        break  # Only first text block per message
            elif isinstance(content, str):
                text = f"Assistant: {content}"

        if not text:
            continue

        # Truncate individual messages
        if len(text) > 500:
            text = text[:500] + "..."

        if total_chars + len(text) > MAX_TRANSCRIPT_CHARS:
            break

        messages.append(text)
        total_chars += len(text)

        if len(messages) >= MAX_TRANSCRIPT_MESSAGES:
            break

    # Reverse back to chronological order
    messages.reverse()
    return "\n\n".join(messages)


def call_openrouter(transcript_text: str, api_key: str) -> str | None:
    """Call OpenRouter API to extract memory from transcript."""
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": f"Here is the conversation transcript:\n\n{transcript_text}"},
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://claude-code-hook.local",
            "X-Title": "PreCompact Memory Save",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT_SECONDS) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError,
            TimeoutError, OSError) as e:
        print(f"[pre-compact-save] API error: {e}", file=sys.stderr)
        return None


def save_to_daily(cwd: Path, extracted: str) -> None:
    """Append extracted memory to daily log file. Deduplicates rapid-fire entries."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    daily_dir = cwd / ".claude" / "memory" / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)

    daily_file = daily_dir / f"{date_str}.md"

    section = f"\n## Pre-Compaction Save ({time_str})\n{extracted}\n"

    if daily_file.exists():
        content = daily_file.read_text(encoding="utf-8")
        content = _dedup_or_append_daily(content, section, now)
    else:
        content = f"# {date_str}\n{section}"

    daily_file.write_text(content, encoding="utf-8")


def _dedup_or_append_daily(content: str, new_section: str, now: datetime) -> str:
    """Replace last Pre-Compaction Save if written <N minutes ago, otherwise append."""
    matches = list(re.finditer(
        r'\n## Pre-Compaction Save \((\d{2}:\d{2})\)\n', content
    ))

    if not matches:
        return content + new_section

    last_match = matches[-1]
    try:
        last_h, last_m = map(int, last_match.group(1).split(":"))
        diff = (now.hour * 60 + now.minute) - (last_h * 60 + last_m)

        if 0 <= diff < DEDUP_WINDOW_MINUTES:
            # Replace the last section instead of appending
            section_start = last_match.start()
            # Find next "## " header or end of file
            next_header = re.search(r'\n## ', content[last_match.end():])
            section_end = (last_match.end() + next_header.start()) if next_header else len(content)
            return content[:section_start] + new_section + content[section_end:]
    except (ValueError, IndexError):
        pass

    return content + new_section


def update_active_context(cwd: Path, extracted: str) -> None:
    """Add a pre-compaction note to activeContext.md session log."""
    now = datetime.now()
    time_str = now.strftime("%H:%M")

    ac_path = cwd / ".claude" / "memory" / "activeContext.md"
    if not ac_path.exists():
        return

    content = ac_path.read_text(encoding="utf-8")

    # Find the Session Log section and add a note
    note = f"\n**[Pre-compaction save {time_str}]** {_extract_did(extracted)}\n"

    # Try to append after the most recent session entry
    if "## Session Log" in content:
        # Add after the first ### entry under Session Log
        lines = content.split("\n")
        insert_idx = None
        in_session_log = False
        for i, line in enumerate(lines):
            if "## Session Log" in line:
                in_session_log = True
            elif in_session_log and line.startswith("### "):
                # Find the end of this session entry's content
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith("### ") or lines[j].startswith("## "):
                        insert_idx = j
                        break
                else:
                    insert_idx = len(lines)
                break

        if insert_idx is not None:
            lines.insert(insert_idx, note)
            content = "\n".join(lines)

    ac_path.write_text(content, encoding="utf-8")


def _extract_did(extracted: str) -> str:
    """Pull out the Did: line from extracted text."""
    for line in extracted.split("\n"):
        if line.strip().startswith("**Did:**"):
            return line.strip().replace("**Did:**", "").strip()
    return extracted.split("\n")[0][:100] if extracted else "session context saved"


def curate_active_context(cwd: Path) -> None:
    """Trim activeContext.md if over line limit.

    Strategy:
    1. If total lines <= limit, do nothing
    2. Remove old date sections from Session Log (keep only current date)
    3. Limit pre-compaction notes to last N within current date
    4. Old data is NOT lost — it lives in daily/ logs
    """
    ac_path = cwd / ".claude" / "memory" / "activeContext.md"
    if not ac_path.exists():
        return

    content = ac_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    if len(lines) <= ACTIVE_CONTEXT_MAX_LINES:
        return  # Under limit, nothing to do

    # --- Phase 1: Remove old date sections from Session Log ---
    session_log_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("## Session Log"):
            session_log_idx = i
            break

    if session_log_idx is None:
        return  # No session log, can't trim structurally

    # Find ### date headers within Session Log
    date_headers = []
    for i in range(session_log_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("### "):
            date_headers.append(i)
        elif stripped.startswith("## ") and not stripped.startswith("### "):
            break  # Hit next top-level section

    if len(date_headers) > 1:
        # Keep only the first (most recent) date section
        second_date_idx = date_headers[1]
        trimmed_count = len(date_headers) - 1

        # Everything before old dates + trimmed note
        new_lines = lines[:second_date_idx]
        new_lines.append(f"")
        new_lines.append(f"> [{trimmed_count} older session(s) archived — see daily/ logs]")

        # Anything after the session log section (unlikely, but safe)
        after_session = []
        for i in range(date_headers[-1], len(lines)):
            stripped = lines[i].strip()
            if stripped.startswith("## ") and not stripped.startswith("### "):
                after_session = lines[i:]
                break

        new_lines.extend(after_session)
        lines = new_lines

    # --- Phase 2: Trim pre-compaction notes in current date ---
    if len(lines) > ACTIVE_CONTEXT_MAX_LINES:
        note_indices = [
            i for i, line in enumerate(lines)
            if "**[Pre-compaction save" in line
        ]
        if len(note_indices) > MAX_PRECOMPACT_NOTES:
            # Remove oldest notes (keep last N)
            to_remove = set(note_indices[:-MAX_PRECOMPACT_NOTES])
            # Also remove adjacent blank lines
            expanded_remove = set()
            for idx in to_remove:
                expanded_remove.add(idx)
                if idx > 0 and lines[idx - 1].strip() == "":
                    expanded_remove.add(idx - 1)
            lines = [line for i, line in enumerate(lines) if i not in expanded_remove]

    ac_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    try:
        # Read hook input from stdin
        raw = sys.stdin.read()
        if not raw.strip():
            return  # No input, nothing to do

        hook_input = json.loads(raw)
        cwd = Path(hook_input.get("cwd", ".")).resolve()

        # Vaultguard: only run in project directories with CLAUDE.md
        if not (cwd / "CLAUDE.md").exists():
            sys.exit(0)

        # Find API key
        api_key = find_api_key(cwd)
        if not api_key:
            print("[pre-compact-save] No API key found, skipping", file=sys.stderr)
            return

        # Find transcript
        transcript_path = find_transcript(hook_input)
        if not transcript_path:
            print("[pre-compact-save] No transcript found, skipping", file=sys.stderr)
            return

        # Read and filter transcript
        transcript_text = read_transcript(transcript_path)
        if not transcript_text:
            print("[pre-compact-save] Empty transcript, skipping", file=sys.stderr)
            return

        # Call LLM to extract key information
        extracted = call_openrouter(transcript_text, api_key)
        if not extracted:
            print("[pre-compact-save] LLM extraction failed, skipping", file=sys.stderr)
            return

        # Save to daily log (with dedup)
        save_to_daily(cwd, extracted)

        # Update activeContext.md
        update_active_context(cwd, extracted)

        # Curate activeContext.md (trim if over limit)
        curate_active_context(cwd)

        print(f"[pre-compact-save] Saved + curated memory files", file=sys.stderr)

    except Exception as e:
        # NEVER block compaction — log and exit cleanly
        print(f"[pre-compact-save] Unexpected error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
    sys.exit(0)  # Always exit 0 — never block compaction
