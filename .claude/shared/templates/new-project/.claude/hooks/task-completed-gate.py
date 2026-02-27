#!/usr/bin/env python3
"""
TaskCompleted Quality Gate Hook

Fires when any agent marks a task as completed (via TaskUpdate).
Runs lightweight code quality checks on modified files.
Exit 2 = BLOCK completion (stderr fed back to the agent as feedback).
Exit 0 = allow completion.

Checks:
1. Python syntax validation (py_compile) on modified .py files
2. Merge conflict markers (<<<, ===, >>>) in modified files
3. Logs all completions to work/task-completions.md

IMPORTANT: Must be fast (<10s). Never run full test suites here.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_modified_files(cwd: Path) -> list[str]:
    """Get list of modified files via git diff (staged + unstaged)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=str(cwd)
        )
        files = [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]

        # Also check staged files
        result2 = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True, text=True, timeout=5, cwd=str(cwd)
        )
        staged = [f.strip() for f in result2.stdout.strip().splitlines() if f.strip()]

        # Also check untracked files
        result3 = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=5, cwd=str(cwd)
        )
        untracked = [f.strip() for f in result3.stdout.strip().splitlines() if f.strip()]

        return list(set(files + staged + untracked))
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []


def check_python_syntax(cwd: Path, files: list[str]) -> list[str]:
    """Check Python files for syntax errors. Returns list of error messages."""
    errors = []
    py_files = [f for f in files if f.endswith(".py")]

    for py_file in py_files:
        full_path = cwd / py_file
        if not full_path.exists():
            continue
        try:
            result = subprocess.run(
                ["py", "-3", "-m", "py_compile", str(full_path)],
                capture_output=True, text=True, timeout=5, cwd=str(cwd)
            )
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                errors.append(f"  {py_file}: {error_msg}")
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

    return errors


def check_merge_conflicts(cwd: Path, files: list[str]) -> list[str]:
    """Check for merge conflict markers in modified files."""
    # Construct markers dynamically to avoid this script detecting itself
    markers = ["<" * 7, "=" * 7, ">" * 7]
    conflicts = []

    for file_path in files:
        # Skip hook scripts (they may contain marker strings in code)
        if ".claude/hooks/" in file_path.replace("\\", "/"):
            continue
        full_path = cwd / file_path
        if not full_path.exists() or full_path.stat().st_size > 500_000:
            continue  # Skip missing or very large files
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            for marker in markers:
                # Only flag markers at line start (real conflicts)
                for line in content.splitlines():
                    if line.startswith(marker):
                        conflicts.append(f"  {file_path}: merge conflict marker at line start")
                        break
                else:
                    continue
                break
        except (OSError, PermissionError):
            pass

    return conflicts


def log_completion(cwd: Path, data: dict, blocked: bool, reason: str = "") -> None:
    """Log task completion to work/task-completions.md."""
    work_dir = cwd / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    log_file = work_dir / "task-completions.md"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    task_id = data.get("task_id", "?")
    task_subject = data.get("task_subject", "unknown")
    teammate = data.get("teammate_name", "main")
    status = "BLOCKED" if blocked else "PASSED"

    entry = f"| {now} | {task_id} | {task_subject[:50]} | {teammate} | {status} |"
    if reason:
        entry += f" {reason[:80]} |"
    entry += "\n"

    if not log_file.exists():
        header = "# Task Completion Log\n\n"
        header += "| Time | Task ID | Subject | Agent | Gate | Notes |\n"
        header += "|------|---------|---------|-------|------|-------|\n"
        log_file.write_text(header + entry, encoding="utf-8")
    else:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)
        cwd = Path(data.get("cwd", ".")).resolve()

        # Vaultguard: only run in project directories with CLAUDE.md
        if not (cwd / "CLAUDE.md").exists():
            sys.exit(0)

        # Get modified files
        modified = get_modified_files(cwd)

        if not modified:
            # No modified files — nothing to check, allow completion
            log_completion(cwd, data, blocked=False, reason="no modified files")
            sys.exit(0)

        # Check 1: Python syntax errors
        syntax_errors = check_python_syntax(cwd, modified)

        # Check 2: Merge conflict markers
        conflict_errors = check_merge_conflicts(cwd, modified)

        # Combine all errors
        all_errors = []
        if syntax_errors:
            all_errors.append("PYTHON SYNTAX ERRORS:")
            all_errors.extend(syntax_errors)
        if conflict_errors:
            all_errors.append("MERGE CONFLICT MARKERS:")
            all_errors.extend(conflict_errors)

        if all_errors:
            # BLOCK completion — exit 2, stderr = feedback to agent
            feedback = "Task completion BLOCKED by quality gate.\n"
            feedback += "\n".join(all_errors)
            feedback += "\n\nFix these issues before marking the task as completed."
            print(feedback, file=sys.stderr)
            log_completion(cwd, data, blocked=True, reason=all_errors[0][:80])
            sys.exit(2)

        # All checks passed
        log_completion(cwd, data, blocked=False)
        sys.exit(0)

    except Exception as e:
        # On error: log but don't block (exit 0)
        print(f"[task-completed-gate] Error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
