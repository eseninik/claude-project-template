#!/usr/bin/env python3
"""Codex Gate — enforces Codex consultation at every decision point.

Two enforcement mechanisms:

1. TaskCreated hook: auto-calls codex-ask.py for every new task
   → Covers: pipeline phases, Agent Teams, subtask decomposition

2. PreToolUse gate (Edit/Write): blocks file modifications if Codex
   wasn't consulted in the last COOLDOWN_MINUTES
   → Forces Claude to call codex-ask.py before making changes
   → Cooldown prevents blocking every single edit (once per burst)

Exit codes:
  0 — allow
  2 — block (Codex consultation required)
"""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    for s in [sys.stdin, sys.stdout, sys.stderr]:
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger("codex-gate")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stderr,
)

MAX_EDITS_PER_CONSULTATION = 5  # After 5 edits, must consult Codex again
COOLDOWN_MINUTES = 5  # Also time-based fallback
CODEX_ASK_SCRIPT = ".claude/scripts/codex-ask.py"

# codex-implement result recognition (tech-spec Section 9)
RESULT_MAX_AGE_SECONDS = 180  # 3 minutes
CODEX_IMPLEMENTATIONS_DIR = "work/codex-implementations"
CODEX_TASKS_DIR = "work/codex-primary/tasks"


def get_project_dir():
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()


def get_last_codex_time(project_dir):
    """Check when Codex was last consulted."""
    opinion_file = project_dir / ".codex" / "reviews" / "parallel-opinion.md"
    timestamp_file = project_dir / ".codex" / "last-consulted"

    # Check both files — use the most recent
    latest = 0
    for f in [opinion_file, timestamp_file]:
        if f.exists():
            latest = max(latest, f.stat().st_mtime)
    return latest


def mark_codex_consulted(project_dir):
    """Mark that Codex was just consulted. Resets edit counter."""
    ts_file = project_dir / ".codex" / "last-consulted"
    ts_file.parent.mkdir(parents=True, exist_ok=True)
    ts_file.write_text(str(time.time()), encoding="utf-8")
    # Reset edit counter
    count_file = project_dir / ".codex" / "edit-count"
    count_file.write_text("0", encoding="utf-8")


def get_edit_count(project_dir):
    """Get number of Edit/Write calls since last Codex consultation."""
    count_file = project_dir / ".codex" / "edit-count"
    if not count_file.exists():
        return 0
    try:
        return int(count_file.read_text().strip())
    except (ValueError, OSError):
        return 0


def increment_edit_count(project_dir):
    """Increment the edit counter."""
    count_file = project_dir / ".codex" / "edit-count"
    count_file.parent.mkdir(parents=True, exist_ok=True)
    current = get_edit_count(project_dir)
    count_file.write_text(str(current + 1), encoding="utf-8")
    return current + 1


def is_codex_fresh(project_dir):
    """Check if Codex opinion is fresh enough.

    Two conditions (BOTH must pass):
    1. Time-based: last consultation < COOLDOWN_MINUTES ago
    2. Count-based: < MAX_EDITS_PER_CONSULTATION edits since last consultation

    If EITHER expires, Codex consultation is required.
    """
    # Time check
    last = get_last_codex_time(project_dir)
    if last == 0:
        return False
    age_minutes = (time.time() - last) / 60
    if age_minutes >= COOLDOWN_MINUTES:
        logger.info("time-based expiry: %.1f min > %d min", age_minutes, COOLDOWN_MINUTES)
        return False

    # Count check
    count = get_edit_count(project_dir)
    if count >= MAX_EDITS_PER_CONSULTATION:
        logger.info("count-based expiry: %d edits >= %d max", count, MAX_EDITS_PER_CONSULTATION)
        return False

    return True


# ---------------------------------------------------------------------------
# codex-implement result recognition (tech-spec Section 9)
# ---------------------------------------------------------------------------

def _parse_result_status(result_path):
    """Read task-N-result.md and return its 'status' field, or None on error.

    Accepts any reasonable layout: YAML frontmatter, bold key, plain line.
    Never raises — parse errors return None so the gate falls back to old behavior.
    """
    try:
        text = result_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        logger.info("result-parse: cannot read %s: %s", result_path.name, e)
        return None

    # Match common "status" emissions: `status: pass`, `**Status:** pass`,
    # `- status: pass`, `> Status = fail`. Strip bold/italic markers from each
    # line first so colon placement inside '**...**' does not break the regex.
    import re
    for raw in text.splitlines():
        # Remove leading bullet/quote, surrounding bold/italic, backticks.
        stripped = raw.lstrip(" \t-*>").strip()
        stripped = stripped.replace("**", "").replace("__", "").replace("`", "")
        m = re.match(r"(?i)status\s*[:=]\s*([A-Za-z0-9_-]+)", stripped)
        if m:
            return m.group(1).strip().lower()
    logger.info("result-parse: no status field in %s", result_path.name)
    return None


def _parse_scope_fence(task_path):
    """Extract 'Allowed paths' from a task-N.md Scope Fence section.

    Returns list of normalized POSIX-style path fragments (strings). Empty list
    on any parse error — caller treats empty fence as 'no match'.
    """
    try:
        text = task_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        logger.info("fence-parse: cannot read %s: %s", task_path.name, e)
        return []

    # Locate "## Scope Fence" section (case-insensitive).
    import re
    fence_match = re.search(r"(?im)^##\s+Scope\s+Fence\s*$", text)
    if not fence_match:
        return []

    # Slice to next top-level heading.
    start = fence_match.end()
    tail = text[start:]
    next_hdr = re.search(r"(?m)^##\s+", tail)
    section = tail[: next_hdr.start()] if next_hdr else tail

    # Find the "Allowed paths" subsection; stop at "Forbidden" or blank run.
    allowed_match = re.search(r"(?is)allowed\s+paths[^\n]*\n(.+?)(?:\n\s*\*{0,2}forbidden|\Z)", section)
    if not allowed_match:
        return []
    allowed_block = allowed_match.group(1)

    paths = []
    for line in allowed_block.splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        # Strip leading "-", backticks, parenthetical annotations like "(new file)".
        entry = line.lstrip("-").strip()
        entry = entry.strip("`").strip()
        # Drop trailing parenthetical: "path/to/x (new)"
        entry = re.sub(r"\s*\([^)]*\)\s*$", "", entry).strip()
        entry = entry.strip("`").strip()
        if not entry:
            continue
        # Normalize to forward slashes for comparison.
        paths.append(entry.replace("\\", "/").rstrip("/"))
    return paths


def _path_in_fence(target_rel_posix, fence_entries):
    """True if target_rel_posix is covered by any fence entry.

    Fence entry can be a file ('a/b/c.py'), a directory ('a/b/'), or a glob
    with '**' wildcard (only simple prefix matching is supported).
    """
    if not fence_entries:
        return False
    target = target_rel_posix.rstrip("/")
    for entry in fence_entries:
        if not entry:
            continue
        # Strip glob tail like '**' or '*'.
        import re
        simple = re.sub(r"/?\*+$", "", entry).rstrip("/")
        if not simple:
            continue
        # Exact file match or directory-prefix match (with '/' boundary).
        if target == simple:
            return True
        if target.startswith(simple + "/"):
            return True
    return False


def _resolve_target_path(project_dir, target_raw):
    """Resolve a tool_input file path to an absolute Path inside project_dir.

    Returns None if the resolved path escapes project_dir (no symlink traversal).
    """
    if not target_raw:
        return None
    try:
        p = Path(target_raw)
        if not p.is_absolute():
            p = project_dir / p
        resolved = p.resolve()
    except (OSError, ValueError) as e:
        logger.info("target-resolve: cannot resolve %s: %s", target_raw, e)
        return None
    try:
        resolved.relative_to(project_dir)
    except ValueError:
        logger.info("target-resolve: %s escapes project root", resolved)
        return None
    return resolved


def _extract_target_path(payload):
    """Pull the file path from Edit/Write tool_input. Returns str or None."""
    if not isinstance(payload, dict):
        return None
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return None
    # Edit, Write, NotebookEdit all use `file_path`; MultiEdit and Write do too.
    return tool_input.get("file_path") or tool_input.get("notebook_path")


def check_task_result_opinion(project_dir, target_rel_posix):
    """Return 'codex-implement' if a fresh in-scope task-*-result.md authorizes
    editing target_rel_posix; else None.

    Decision rules (all must hold for acceptance):
      1. target_rel_posix is non-empty
      2. Some task-{N}-result.md in work/codex-implementations/ has mtime
         within RESULT_MAX_AGE_SECONDS of now
      3. That file contains status=pass (case-insensitive)
      4. The paired work/codex-primary/tasks/T{N}-*.md declares a Scope Fence
         that covers target_rel_posix

    Never raises — any exception returns None so caller falls through to old
    behavior. Fall-through is explicit via the outer try/except.
    """
    try:
        if not target_rel_posix:
            return None
        results_dir = project_dir / CODEX_IMPLEMENTATIONS_DIR
        if not results_dir.is_dir():
            logger.info("codex-implement: no results dir, skip new-path check")
            return None
        tasks_dir = project_dir / CODEX_TASKS_DIR
        if not tasks_dir.is_dir():
            logger.info("codex-implement: no tasks dir, skip new-path check")
            return None

        now = time.time()
        import re
        fresh_matches = []
        for result_path in results_dir.glob("task-*-result.md"):
            try:
                age = now - result_path.stat().st_mtime
            except OSError:
                continue
            if age > RESULT_MAX_AGE_SECONDS:
                continue

            # Symlink safety: ensure resolved path stays inside project root.
            try:
                rp = result_path.resolve()
                rp.relative_to(project_dir)
            except (OSError, ValueError):
                logger.info("codex-implement: skip %s (outside project)", result_path.name)
                continue

            status = _parse_result_status(result_path)
            if status != "pass":
                logger.info(
                    "codex-implement: skip %s (status=%s, age=%.1fs)",
                    result_path.name, status, age,
                )
                continue

            # Extract task id from filename: task-{N}-result.md (N may be
            # numeric like '1' or a slug like 'T5-codex-gate').
            m = re.match(r"task-(.+?)-result\.md$", result_path.name)
            if not m:
                continue
            task_id = m.group(1)
            fresh_matches.append((task_id, age))

        if not fresh_matches:
            return None

        # For each fresh pass result, look up the paired task file and check fence.
        for task_id, age in sorted(fresh_matches, key=lambda x: x[1]):
            # Task file naming in this repo: T{ID}-*.md, tN-*.md, or task-{ID}.md
            candidates = []
            for pattern in (f"T{task_id}-*.md", f"{task_id}-*.md", f"task-{task_id}.md", f"task-{task_id}-*.md"):
                candidates.extend(tasks_dir.glob(pattern))
            # Deduplicate while preserving order.
            seen = set()
            unique = []
            for c in candidates:
                if c not in seen:
                    seen.add(c)
                    unique.append(c)
            if not unique:
                logger.info("codex-implement: no task file for id=%s", task_id)
                continue

            for task_path in unique:
                fence = _parse_scope_fence(task_path)
                if not fence:
                    logger.info("codex-implement: task %s has empty fence", task_path.name)
                    continue
                if _path_in_fence(target_rel_posix, fence):
                    logger.info(
                        "codex-implement: MATCH task=%s target=%s age=%.1fs",
                        task_id, target_rel_posix, age,
                    )
                    return "codex-implement"
                logger.info(
                    "codex-implement: task=%s target=%s NOT in fence (%d entries)",
                    task_id, target_rel_posix, len(fence),
                )
        return None
    except Exception as e:
        # Never crash the gate — log and fall back to old behavior.
        logger.warning("codex-implement: unexpected error, falling back: %s", e)
        return None


def call_codex_for_task(project_dir, task_text):
    """Call codex-ask.py synchronously for a task."""
    script = project_dir / CODEX_ASK_SCRIPT
    if not script.exists():
        logger.warning("codex-ask.py not found at %s", script)
        return None

    try:
        result = subprocess.run(
            [sys.executable, str(script), task_text],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120, cwd=str(project_dir),
        )
        if result.returncode == 0 and result.stdout.strip():
            mark_codex_consulted(project_dir)
            return result.stdout.strip()
    except Exception as e:
        logger.warning("codex-ask failed: %s", e)
    return None


# ---------------------------------------------------------------------------
# Hook handlers
# ---------------------------------------------------------------------------

def handle_task_created(payload):
    """Auto-call Codex when a new task is created."""
    project_dir = get_project_dir()

    # Extract task info
    subject = ""
    description = ""
    if isinstance(payload, dict):
        tool_input = payload.get("tool_input", {})
        subject = tool_input.get("subject", "")
        description = tool_input.get("description", "")

    if not subject and not description:
        logger.info("no task info, skipping")
        return

    task_text = f"New task: {subject}. {description}"
    logger.info("auto-consulting Codex for task: %s", subject[:80])

    opinion = call_codex_for_task(project_dir, task_text)

    if opinion:
        output = {
            "systemMessage": f"Codex opinion on this task:\n{opinion}"
        }
        print(json.dumps(output, ensure_ascii=False))
        logger.info("Codex opinion for task delivered (%d chars)", len(opinion))


def handle_pre_tool_use(payload):
    """Block Edit/Write if Codex wasn't consulted recently."""
    project_dir = get_project_dir()

    # Only gate Edit and Write
    tool_name = ""
    if isinstance(payload, dict):
        tool_name = payload.get("tool_name", "")

    if tool_name not in ("Edit", "Write"):
        sys.exit(0)

    # New path: accept a fresh in-scope codex-implement result (tech-spec 9.2).
    # Resolve target file path from tool_input; anchor under project root.
    target_raw = _extract_target_path(payload)
    target_abs = _resolve_target_path(project_dir, target_raw)
    target_rel_posix = None
    if target_abs is not None:
        try:
            target_rel_posix = target_abs.relative_to(project_dir).as_posix()
        except ValueError:
            target_rel_posix = None

    implement_source = check_task_result_opinion(project_dir, target_rel_posix)
    if implement_source:
        count = increment_edit_count(project_dir)
        logger.info(
            "codex fresh via %s, allowing %s target=%s (edit %d/%d)",
            implement_source, tool_name, target_rel_posix, count, MAX_EDITS_PER_CONSULTATION,
        )
        sys.exit(0)

    # Fallback: old codex-ask.py freshness check (preserves prior behavior).
    if is_codex_fresh(project_dir):
        count = increment_edit_count(project_dir)
        logger.info(
            "codex fresh via codex-ask, allowing %s (edit %d/%d)",
            tool_name, count, MAX_EDITS_PER_CONSULTATION,
        )
        sys.exit(0)

    # Neither opinion source is fresh — block and require consultation.
    logger.warning("codex opinion stale (source=none-stale), blocking %s", tool_name)
    msg = (
        "Codex gate: opinion is stale (>3 min). "
        "Run `py -3 .claude/scripts/codex-ask.py \"your task\"` first, "
        "then retry this edit."
    )
    print(msg, file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Hook profile gate
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from hook_base import should_run
        if not should_run("codex-gate"):
            sys.exit(0)
    except ImportError:
        pass

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    # Detect event from argv
    event = sys.argv[1] if len(sys.argv) > 1 else ""

    if event == "TaskCreated":
        handle_task_created(payload)
    elif event == "PreToolUse":
        handle_pre_tool_use(payload)
    else:
        # Auto-detect from payload
        if isinstance(payload, dict) and payload.get("tool_name"):
            handle_pre_tool_use(payload)
        elif isinstance(payload, dict) and payload.get("tool_input", {}).get("subject"):
            handle_task_created(payload)

    sys.exit(0)


if __name__ == "__main__":
    main()
