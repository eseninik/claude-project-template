#!/usr/bin/env python3
"""
Tests for curation logic in pre-compact-save.py

Tests 3 features WITHOUT calling OpenRouter API:
1. Daily dedup (_dedup_or_append_daily)
2. activeContext rotation (curate_active_context)
3. Pre-compaction note limit (curate_active_context)
4. No regression — small file untouched
"""

import importlib.util
import sys
import tempfile
import textwrap
from datetime import datetime
from pathlib import Path

# --- Import the hook module dynamically ---
HOOK_PATH = Path(__file__).parent / "pre-compact-save.py"
spec = importlib.util.spec_from_file_location("pre_compact_save", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

# Pull out the functions we need
_dedup_or_append_daily = hook._dedup_or_append_daily
curate_active_context = hook.curate_active_context

results = []


def report(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    results.append((name, passed))
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


# ============================================================
# Test 1: Daily dedup
# ============================================================
print("\n=== Test 1: Daily dedup (_dedup_or_append_daily) ===")

# Setup: existing content with a Pre-Compaction Save from 14:30
existing_content = textwrap.dedent("""\
    # 2026-02-23

    ## Pre-Compaction Save (14:30)
    **Did:** Implemented feature X
    **Decided:** Use approach A
    **Learned:** Pattern Y works well
    **Next:** Continue with Z
""")

new_section_replace = textwrap.dedent("""\

    ## Pre-Compaction Save (14:32)
    **Did:** Continued feature X
    **Decided:** Refined approach A
    **Learned:** none
    **Next:** Test everything
""")

new_section_append = textwrap.dedent("""\

    ## Pre-Compaction Save (14:40)
    **Did:** Fixed bug in feature X
    **Decided:** none
    **Learned:** Edge case in module M
    **Next:** Deploy
""")

# Test 1a: Should REPLACE (14:32 is 2 min after 14:30 — within 5 min window)
now_replace = datetime(2026, 2, 23, 14, 32)
result_replace = _dedup_or_append_daily(existing_content, new_section_replace, now_replace)

count_headers_replace = result_replace.count("## Pre-Compaction Save")
has_new_content = "14:32" in result_replace
has_old_content = "14:30" not in result_replace  # old one should be gone

report(
    "1a: Replace within dedup window (2 min)",
    count_headers_replace == 1 and has_new_content and has_old_content,
    f"headers={count_headers_replace}, has_14:32={has_new_content}, no_14:30={has_old_content}"
)

# Test 1b: Should APPEND (14:40 is 10 min after 14:30 — outside 5 min window)
now_append = datetime(2026, 2, 23, 14, 40)
result_append = _dedup_or_append_daily(existing_content, new_section_append, now_append)

count_headers_append = result_append.count("## Pre-Compaction Save")
has_both = "14:30" in result_append and "14:40" in result_append

report(
    "1b: Append outside dedup window (10 min)",
    count_headers_append == 2 and has_both,
    f"headers={count_headers_append}, has_both={has_both}"
)

# Test 1c: No existing Pre-Compaction Save entries — should append
empty_content = "# 2026-02-23\n\nSome other content.\n"
now_first = datetime(2026, 2, 23, 15, 0)
new_section_first = "\n## Pre-Compaction Save (15:00)\n**Did:** First save\n"
result_first = _dedup_or_append_daily(empty_content, new_section_first, now_first)

report(
    "1c: First entry — append to empty",
    "15:00" in result_first and result_first.count("## Pre-Compaction Save") == 1,
    f"has_15:00={'15:00' in result_first}"
)

# Test 1d: Exact boundary — 5 min should NOT dedup (only < 5)
existing_5min = textwrap.dedent("""\
    # 2026-02-23

    ## Pre-Compaction Save (14:30)
    **Did:** Something
""")
now_boundary = datetime(2026, 2, 23, 14, 35)
new_section_boundary = "\n## Pre-Compaction Save (14:35)\n**Did:** Boundary test\n"
result_boundary = _dedup_or_append_daily(existing_5min, new_section_boundary, now_boundary)

report(
    "1d: Exact 5 min boundary — should append",
    result_boundary.count("## Pre-Compaction Save") == 2,
    f"headers={result_boundary.count('## Pre-Compaction Save')}"
)


# ============================================================
# Test 2: activeContext rotation (curate_active_context)
# ============================================================
print("\n=== Test 2: activeContext rotation ===")

with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)
    mem_dir = tmpdir / ".claude" / "memory"
    mem_dir.mkdir(parents=True)

    # Build a 220+ line activeContext.md
    header = textwrap.dedent("""\
        # Active Context

        ## Current Focus
        - Working on feature X
        - Testing hook scripts
        - Pipeline automation
        - Memory management improvements
        - Code review pending
        - Documentation updates needed
        - Performance optimization
        - Bug fix for issue #42
        - Integration testing
        - Deployment preparation
        - Monitoring setup
        - Error handling improvements
        - Logging enhancements
        - Security audit
        - API versioning
        - Database migration plan
        - Cache invalidation strategy
        - Rate limiting implementation
        - Feature flag management
        - A/B testing framework

        ## Recent Decisions
        - ADR-001: Use Python for hooks
        - ADR-002: Use OpenRouter for LLM calls
        - ADR-003: Graphiti for knowledge graph
        - ADR-004: Pre-compaction saves
        - ADR-005: Daily log format
        - ADR-006: Curation strategy
        - ADR-007: Agent team structure
        - ADR-008: Pipeline phases
        - ADR-009: QA validation loop
        - ADR-010: Skill mapping
        - ADR-011: Memory architecture
        - ADR-012: Hook execution order
        - ADR-013: Error recovery
        - ADR-014: Context compression
        - ADR-015: Template versioning
        - ADR-016: Branch strategy
        - ADR-017: Commit conventions
        - ADR-018: Test coverage targets
        - ADR-019: Monitoring approach
        - ADR-020: Alerting thresholds

    """)

    session_log = "## Session Log\n"

    # Current date — 50 lines
    session_log += "### 2026-02-23\n"
    for i in range(1, 51):
        session_log += f"- Activity {i} on current date\n"

    # Older date 1 — 50 lines
    session_log += "\n### 2026-02-22\n"
    for i in range(1, 51):
        session_log += f"- Activity {i} on yesterday\n"

    # Older date 2 — 50 lines
    session_log += "\n### 2026-02-19\n"
    for i in range(1, 51):
        session_log += f"- Activity {i} on Feb 19\n"

    full_content = header + session_log
    lines_before = len(full_content.split("\n"))

    ac_path = mem_dir / "activeContext.md"
    ac_path.write_text(full_content, encoding="utf-8")

    # Verify we have a file over 150 lines
    report(
        "2-setup: File has 200+ lines",
        lines_before > 200,
        f"actual={lines_before} lines"
    )

    # Run curation
    curate_active_context(tmpdir)

    # Read result
    result = ac_path.read_text(encoding="utf-8")
    lines_after = len(result.split("\n"))

    # Checks
    has_current_date = "### 2026-02-23" in result
    has_old_date_1 = "### 2026-02-22" in result
    has_old_date_2 = "### 2026-02-19" in result
    has_archive_note = "older session(s) archived" in result
    trimmed = lines_after <= 150

    report(
        "2a: Current date section kept",
        has_current_date,
        f"found={'### 2026-02-23' in result}"
    )
    report(
        "2b: Old date sections removed",
        not has_old_date_1 and not has_old_date_2,
        f"2022={has_old_date_1}, 2019={has_old_date_2}"
    )
    report(
        "2c: Archive note added",
        has_archive_note,
        f"found={has_archive_note}"
    )
    report(
        "2d: Trimmed to ~150 lines or less",
        trimmed,
        f"lines_before={lines_before}, lines_after={lines_after}"
    )


# ============================================================
# Test 3: Pre-compaction note limit
# ============================================================
print("\n=== Test 3: Pre-compaction note limit ===")

with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)
    mem_dir = tmpdir / ".claude" / "memory"
    mem_dir.mkdir(parents=True)

    # Build a file with 6 pre-compaction notes, making it 200+ lines
    header = textwrap.dedent("""\
        # Active Context

        ## Current Focus
        - Working on feature X
        - Pipeline automation
        - Memory management
        - Code review
        - Documentation updates
        - Performance optimization
        - Bug fix for issue #42
        - Integration testing
        - Deployment preparation
        - Monitoring setup

        ## Recent Decisions
        - ADR-001: Decision one
        - ADR-002: Decision two
        - ADR-003: Decision three
        - ADR-004: Decision four
        - ADR-005: Decision five

    """)

    session_log = "## Session Log\n### 2026-02-23\n"

    # Add 6 pre-compaction notes
    for i in range(1, 7):
        session_log += f"\n**[Pre-compaction save {10+i}:{i:02d}]** Did thing #{i} in the session\n"

    # Pad with regular activity lines to reach 200+ total
    for i in range(1, 171):
        session_log += f"- Regular activity line {i}\n"

    full_content = header + session_log
    lines_before = len(full_content.split("\n"))

    ac_path = mem_dir / "activeContext.md"
    ac_path.write_text(full_content, encoding="utf-8")

    count_notes_before = full_content.count("**[Pre-compaction save")
    report(
        "3-setup: 6 pre-compaction notes + 200+ lines",
        count_notes_before == 6 and lines_before > 200,
        f"notes={count_notes_before}, lines={lines_before}"
    )

    # Run curation
    curate_active_context(tmpdir)

    result = ac_path.read_text(encoding="utf-8")
    count_notes_after = result.count("**[Pre-compaction save")
    lines_after = len(result.split("\n"))

    # The 3 oldest should be removed, keeping the last 3
    has_note_4 = "thing #4" in result
    has_note_5 = "thing #5" in result
    has_note_6 = "thing #6" in result
    has_note_1 = "thing #1" in result
    has_note_2 = "thing #2" in result
    has_note_3 = "thing #3" in result

    report(
        "3a: Only 3 pre-compaction notes remain",
        count_notes_after == 3,
        f"notes_before={count_notes_before}, notes_after={count_notes_after}"
    )
    report(
        "3b: Kept last 3 notes (#4, #5, #6)",
        has_note_4 and has_note_5 and has_note_6,
        f"#4={has_note_4}, #5={has_note_5}, #6={has_note_6}"
    )
    report(
        "3c: Removed oldest 3 notes (#1, #2, #3)",
        not has_note_1 and not has_note_2 and not has_note_3,
        f"#1={has_note_1}, #2={has_note_2}, #3={has_note_3}"
    )


# ============================================================
# Test 4: No regression — small file untouched
# ============================================================
print("\n=== Test 4: No regression — small file untouched ===")

with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)
    mem_dir = tmpdir / ".claude" / "memory"
    mem_dir.mkdir(parents=True)

    # Build a small activeContext.md (80 lines)
    small_lines = ["# Active Context", ""]
    small_lines.append("## Current Focus")
    for i in range(1, 21):
        small_lines.append(f"- Focus item {i}")
    small_lines.append("")
    small_lines.append("## Recent Decisions")
    for i in range(1, 11):
        small_lines.append(f"- Decision {i}")
    small_lines.append("")
    small_lines.append("## Session Log")
    small_lines.append("### 2026-02-23")
    for i in range(1, 41):
        small_lines.append(f"- Activity {i}")

    small_content = "\n".join(small_lines) + "\n"
    line_count = len(small_content.split("\n"))

    ac_path = mem_dir / "activeContext.md"
    ac_path.write_text(small_content, encoding="utf-8")

    report(
        "4-setup: File has ~80 lines (under 150 limit)",
        line_count < 150,
        f"lines={line_count}"
    )

    # Run curation
    curate_active_context(tmpdir)

    result = ac_path.read_text(encoding="utf-8")

    report(
        "4a: Content unchanged",
        result == small_content,
        f"unchanged={result == small_content}, len_before={len(small_content)}, len_after={len(result)}"
    )


# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 50)
total = len(results)
passed = sum(1 for _, p in results if p)
failed = total - passed
print(f"  Results: {passed}/{total} passed, {failed} failed")

if failed > 0:
    print("\n  FAILED tests:")
    for name, p in results:
        if not p:
            print(f"    - {name}")

print("=" * 50)
sys.exit(0 if failed == 0 else 1)
