#!/usr/bin/env python3
"""
Codex parallel advisor — runs on Stop hook.
Two modes:
  1. CODE REVIEW: git changes detected → structured JSON review via --output-schema
  2. CONTEXT OPINION: .codex/current-task.md exists → free-form Codex opinion on any task

Codex CLI v0.117.0 flags:
  --sandbox read-only, --full-auto, -m gpt-5.4,
  --output-schema FILE, -o FILE, --ephemeral
  NO --ask-for-approval (removed in v0.117.0)
"""

import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("codex-review")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stderr,
)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def get_changed_files():
    """Get list of changed + untracked files."""
    changed = []
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, timeout=10
        )
        changed = result.stdout.strip().splitlines()
    except Exception:
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True, text=True, timeout=10
            )
            changed = result.stdout.strip().splitlines()
        except Exception:
            pass

    try:
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=10
        )
        untracked = result.stdout.strip().splitlines()
        if untracked:
            changed.extend(untracked)
    except Exception:
        pass

    return changed


SENSITIVE_PATTERNS = [
    "auth", "token", "secret", "password", "credential", "payment",
    "migration", "session", "cookie", "key", "cert", "private",
    "env", "config",
]


def has_high_risk_files(changed_files):
    """Check if any changed files are high-risk.

    Low-risk extensions skip review UNLESS the filename contains
    sensitive patterns (token, secret, auth, payment, migration, etc).
    """
    low_risk_exts = {".md", ".css", ".json", ".txt", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".gitignore"}
    for f in changed_files:
        name_lower = Path(f).name.lower()
        # Always review files with sensitive names regardless of extension
        if any(pat in name_lower for pat in SENSITIVE_PATTERNS):
            return True
        if Path(f).suffix not in low_risk_exts:
            return True
    return False


def run_code_review(project_dir, schema, out_dir, codex_bin="codex"):
    """Mode 1: Structured code review with JSON schema output."""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = out_dir / f"review-{ts}.json"

    codex_args = [
        codex_bin, "exec",
        "Review the current working tree changes. Focus on correctness, security, "
        "performance, and missing tests. Use AGENTS.md rubric if present. "
        "Return JSON matching the schema.",
        "--sandbox", "read-only",
        "--full-auto",
        "-m", "gpt-5.4",
        "--output-schema", str(schema),
        "-o", str(out_file),
        "--ephemeral",
    ]
    logger.info("running code review: %s", " ".join(codex_args[:4]))

    try:
        result = subprocess.run(codex_args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        if result.returncode != 0:
            logger.error("codex review failed (exit %d)", result.returncode)
            return None
    except (subprocess.TimeoutExpired, Exception) as e:
        logger.error("codex review error: %s", e)
        return None

    shutil.copy2(str(out_file), str(out_dir / "latest.json"))

    try:
        return json.loads(out_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def run_context_opinion(project_dir, context_text, codex_bin="codex"):
    """Mode 2: Free-form opinion based on task context (no code changes required)."""
    out_file = project_dir / ".codex" / "reviews" / "opinion-latest.txt"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    prompt = (
        f"You are a parallel advisor. Another AI agent (Claude) just worked on this task. "
        f"Give your independent opinion, alternative suggestions, or additional considerations. "
        f"Be concise (max 10 lines). Focus on what the other agent might have missed.\n\n"
        f"Task context:\n{context_text}"
    )

    codex_args = [
        codex_bin, "exec", prompt,
        "--sandbox", "read-only",
        "--full-auto",
        "-m", "gpt-5.4",
        "-o", str(out_file),
        "--ephemeral",
    ]
    logger.info("running context opinion")

    try:
        result = subprocess.run(codex_args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if result.returncode != 0:
            logger.error("codex opinion failed (exit %d)", result.returncode)
            return None
    except (subprocess.TimeoutExpired, Exception) as e:
        logger.error("codex opinion error: %s", e)
        return None

    try:
        return out_file.read_text(encoding="utf-8").strip()
    except Exception:
        return None


def main():
    # Hook profile gate
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from hook_base import should_run
        if not should_run("codex-review"):
            sys.exit(0)
    except ImportError:
        pass

    logger.info("codex-review hook started")
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            logger.debug("empty stdin, exiting")
            sys.exit(0)

        payload = json.loads(raw)

        # Guard: prevent infinite loop (second Stop after presenting Codex opinion)
        if payload.get("stop_hook_active", False):
            logger.debug("stop_hook_active flag set, skipping to prevent loop")
            sys.exit(0)

        # Check if codex is installed (also check npm global path on Windows)
        codex_bin = shutil.which("codex")
        if not codex_bin:
            # Try common npm global install location on Windows
            npm_codex = Path.home() / "AppData" / "Roaming" / "npm" / "codex.cmd"
            if npm_codex.exists():
                codex_bin = str(npm_codex)
                logger.info("found codex at npm global path: %s", codex_bin)
            else:
                logger.warning("codex CLI not installed, skipping")
                sys.exit(0)

        project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
        schema = project_dir / ".codex" / "review-schema.json"
        out_dir = project_dir / ".codex" / "reviews"
        context_file = project_dir / ".codex" / "current-task.md"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Determine mode
        changed_files = get_changed_files()
        has_code_changes = changed_files and has_high_risk_files(changed_files)
        has_context = context_file.exists()

        # Read context file (delete AFTER Codex completes, not before)
        context_text = ""
        if has_context:
            try:
                context_text = context_file.read_text(encoding="utf-8").strip()
                logger.info("read context file (%d chars)", len(context_text))
            except Exception as exc:
                logger.debug("failed to read context file: %s", exc)
                has_context = False

        # Skip if nothing to review
        if not has_code_changes and not has_context:
            logger.info("no code changes and no context file, skipping")
            sys.exit(0)

        # MODE 1: Code review (structured JSON)
        if has_code_changes and schema.exists():
            logger.info("mode: CODE REVIEW (%d changed files)", len(changed_files))
            review = run_code_review(project_dir, schema, out_dir, codex_bin)

            if review:
                # Clean up context file after successful review
                try:
                    context_file.unlink(missing_ok=True)
                except Exception:
                    pass
                findings = review.get("findings", [])
                verdict = review.get("verdict", {}).get("status", "unknown")
                # Derive blocking from actual findings, not summary.has_blockers
                # (Codex JSON may be inconsistent between summary and findings)
                blockers = [f for f in findings if f.get("severity") == "BLOCKER"]
                has_blockers = len(blockers) > 0
                important_count = sum(1 for f in findings if f.get("severity") == "IMPORTANT")

                if has_blockers:
                    details = "\n".join(
                        f"  - [{f.get('location', {}).get('path', '?')}:{f.get('location', {}).get('line_start', '?')}] "
                        f"{f.get('title', '?')}: {f.get('explanation', '')}"
                        for f in blockers
                    )
                    output = {
                        "decision": "block",
                        "reason": (
                            f"--- Codex gpt-5.4 Code Review ---\n"
                            f"Verdict: {verdict} | BLOCKERs: {len(blockers)} | IMPORTANTs: {important_count}\n"
                            f"{details}\n"
                            f"Read .codex/reviews/latest.json for full details. Fix blockers before completing.\n"
                            f"---"
                        )
                    }
                    print(json.dumps(output))
                elif important_count > 0:
                    # Non-blocking: surface findings as context, NOT as block
                    important_summary = "\n".join(
                        f"  - [{f.get('location', {}).get('path', '?')}] {f.get('title', '?')}"
                        for f in findings if f.get("severity") == "IMPORTANT"
                    )
                    logger.info(
                        "codex review: %s, %d IMPORTANT findings (non-blocking)",
                        verdict, important_count,
                    )
                    # Print as stderr info for Claude to see, but don't block
                    print(
                        f"--- Codex gpt-5.4 Code Review ---\n"
                        f"Verdict: {verdict} | IMPORTANTs: {important_count}\n"
                        f"{important_summary}\n"
                        f"See .codex/reviews/latest.json for details\n---",
                        file=sys.stderr,
                    )
                else:
                    logger.info("codex code review: %s, clean", verdict)

        # MODE 2: Context-based opinion (any task, no code changes needed)
        elif has_context and context_text:
            logger.info("mode: CONTEXT OPINION")
            opinion = run_context_opinion(project_dir, context_text, codex_bin)

            if opinion:
                # Clean up context file AFTER successful Codex call
                try:
                    context_file.unlink(missing_ok=True)
                except Exception:
                    pass
                # Non-blocking: surface opinion as stderr info, NOT as block
                logger.info("codex context opinion received (%d chars)", len(opinion))
                print(
                    f"--- Codex gpt-5.4 Opinion ---\n"
                    f"{opinion}\n"
                    f"---",
                    file=sys.stderr,
                )
            else:
                logger.info("codex opinion returned empty, skipping")

    except Exception as e:
        logger.error("unexpected error: %s", e, exc_info=True)

    sys.exit(0)


if __name__ == "__main__":
    main()
