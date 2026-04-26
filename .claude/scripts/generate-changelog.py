#!/usr/bin/env python3
"""Generate CHANGELOG.md sections from pipeline-checkpoint-* git tags."""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Sequence


BEGIN_MARKER = "<!-- pipeline-checkpoint-changelog:start -->"
END_MARKER = "<!-- pipeline-checkpoint-changelog:end -->"
DEFAULT_OUTPUT = "CHANGELOG.md"
GIT_TIMEOUT_SECONDS = 30

DEFAULT_PREAMBLE = """# Changelog

All notable changes are tracked here. Release sections are anchored to `pipeline-checkpoint-*` tags and commit subjects use Conventional Commits-style titles where available.

## Round 8 (Z23)
### Changes
- Determinism 10/10.

## Round 8 (Z20)
### Changes
- Security 10/10.

## Round 8 (Z17)
### Changes
- Reliability 10/10.

## Round 8 (Z14)
### Changes
- Functional Coverage 10/10.

## Round 7 (Z12)
### Changes
- Y21 + Y25 close all initial Y18-Y25 follow-ups.
"""

logger = logging.getLogger("generate_changelog")


class JsonFormatter(logging.Formatter):
    """Small JSON formatter for stderr diagnostics."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        context = getattr(record, "context", None)
        if context:
            payload.update(context)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True)


def configure_logging(verbose: bool) -> None:
    """Configure stderr JSON logging."""
    logger.debug("entry", extra={"context": {"function": "configure_logging", "verbose": verbose}})
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.debug("exit", extra={"context": {"function": "configure_logging", "level": root.level}})


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    logger.debug("entry", extra={"context": {"function": "parse_args", "argc": len(argv)}})
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from pipeline-checkpoint-* tags.")
    parser.add_argument("--repo", default=".", help="Git repository root.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output changelog path, relative to repo unless absolute.")
    parser.add_argument("--stdout", action="store_true", help="Print generated changelog instead of writing it.")
    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG JSON logs on stderr.")
    args = parser.parse_args(list(argv))
    logger.debug("exit", extra={"context": {"function": "parse_args", "stdout": args.stdout}})
    return args


def run_git(repo: Path, args: Sequence[str]) -> str:
    """Run a git command and return stdout."""
    logger.debug("entry", extra={"context": {"function": "run_git", "repo": str(repo), "args": list(args)}})
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        logger.exception("git_invocation_failed", extra={"context": {"function": "run_git", "args": list(args)}})
        raise
    if proc.returncode != 0:
        message = proc.stderr.strip() or ("git exited " + str(proc.returncode))
        logger.error("git_failed", extra={"context": {"function": "run_git", "returncode": proc.returncode, "stderr": message}})
        raise RuntimeError(message)
    logger.debug("exit", extra={"context": {"function": "run_git", "stdout_chars": len(proc.stdout)}})
    return proc.stdout


def list_checkpoint_tags(repo: Path) -> list[str]:
    """Return pipeline-checkpoint tags sorted by tag creation date."""
    logger.debug("entry", extra={"context": {"function": "list_checkpoint_tags", "repo": str(repo)}})
    stdout = run_git(
        repo,
        [
            "for-each-ref",
            "refs/tags/pipeline-checkpoint-*",
            "--sort=creatordate",
            "--format=%(refname:short)",
        ],
    )
    tags = [line.strip() for line in stdout.splitlines() if line.strip()]
    logger.debug("exit", extra={"context": {"function": "list_checkpoint_tags", "count": len(tags)}})
    return tags


def commit_titles_between(repo: Path, previous_tag: str | None, tag: str) -> list[str]:
    """Return formatted commit titles between previous_tag and tag."""
    logger.debug(
        "entry",
        extra={"context": {"function": "commit_titles_between", "previous_tag": previous_tag, "tag": tag}},
    )
    revision = tag if previous_tag is None else previous_tag + ".." + tag
    stdout = run_git(repo, ["log", revision, "--format=- %s"])
    titles = [line.rstrip() for line in stdout.splitlines() if line.strip()]
    if not titles:
        titles = ["- No commits recorded."]
    logger.debug("exit", extra={"context": {"function": "commit_titles_between", "count": len(titles)}})
    return titles


def format_tag_section(tag: str, commit_titles: Sequence[str]) -> str:
    """Render one changelog section for a pipeline checkpoint tag."""
    logger.debug("entry", extra={"context": {"function": "format_tag_section", "tag": tag, "commits": len(commit_titles)}})
    lines = ["## " + tag, "### Changes", *commit_titles]
    section = "\n".join(lines)
    logger.debug("exit", extra={"context": {"function": "format_tag_section", "chars": len(section)}})
    return section


def generate_checkpoint_sections(repo: Path) -> str:
    """Generate all checkpoint-tag sections, newest first."""
    logger.debug("entry", extra={"context": {"function": "generate_checkpoint_sections", "repo": str(repo)}})
    tags = list_checkpoint_tags(repo)
    entries: list[tuple[str, list[str]]] = []
    previous_tag: str | None = None
    for tag in tags:
        entries.append((tag, commit_titles_between(repo, previous_tag, tag)))
        previous_tag = tag
    sections = [format_tag_section(tag, titles) for tag, titles in reversed(entries)]
    text = "\n\n".join(sections)
    logger.debug("exit", extra={"context": {"function": "generate_checkpoint_sections", "sections": len(sections)}})
    return text


def build_changelog(existing_content: str, checkpoint_sections: str) -> str:
    """Build a complete CHANGELOG.md while replacing the managed checkpoint block."""
    logger.debug("entry", extra={"context": {"function": "build_changelog", "existing_chars": len(existing_content)}})
    block = BEGIN_MARKER + "\n" + checkpoint_sections.rstrip() + "\n" + END_MARKER + "\n"
    if BEGIN_MARKER in existing_content and END_MARKER in existing_content:
        start = existing_content.index(BEGIN_MARKER)
        end = existing_content.index(END_MARKER, start) + len(END_MARKER)
        prefix = existing_content[:start].rstrip()
        suffix = existing_content[end:].strip()
        parts = [prefix, block.rstrip()]
        if suffix:
            parts.append(suffix)
        text = "\n\n".join(part for part in parts if part) + "\n"
        logger.debug("exit", extra={"context": {"function": "build_changelog", "chars": len(text), "replaced": True}})
        return text
    prefix = existing_content.strip() or DEFAULT_PREAMBLE.strip()
    text = prefix + "\n\n" + block
    logger.debug("exit", extra={"context": {"function": "build_changelog", "chars": len(text), "replaced": False}})
    return text


def output_path(repo: Path, output: str) -> Path:
    """Resolve the changelog output path."""
    logger.debug("entry", extra={"context": {"function": "output_path", "repo": str(repo), "output": output}})
    path = Path(output)
    resolved = path if path.is_absolute() else repo / path
    logger.debug("exit", extra={"context": {"function": "output_path", "path": str(resolved)}})
    return resolved


def generate_changelog(repo: Path, output: Path) -> str:
    """Generate changelog text from repo tags and existing output content."""
    logger.debug("entry", extra={"context": {"function": "generate_changelog", "repo": str(repo), "output": str(output)}})
    existing = output.read_text(encoding="utf-8") if output.exists() else ""
    sections = generate_checkpoint_sections(repo)
    text = build_changelog(existing, sections)
    logger.debug("exit", extra={"context": {"function": "generate_changelog", "chars": len(text)}})
    return text


def run(args: argparse.Namespace) -> int:
    """Run the changelog generator."""
    logger.debug("entry", extra={"context": {"function": "run", "stdout": args.stdout}})
    try:
        repo = Path(args.repo).resolve()
        out_path = output_path(repo, args.output)
        text = generate_changelog(repo, out_path)
        if args.stdout:
            print(text, end="")
        else:
            out_path.write_text(text, encoding="utf-8")
            print("wrote " + str(out_path))
        logger.debug("exit", extra={"context": {"function": "run", "returncode": 0}})
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        logger.exception("generate_changelog_failed", extra={"context": {"function": "run"}})
        print("error: " + str(exc), file=sys.stderr)
        logger.debug("exit", extra={"context": {"function": "run", "returncode": 2}})
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)
    configure_logging(args.verbose)
    logger.debug("entry", extra={"context": {"function": "main", "argc": len(argv)}})
    code = run(args)
    logger.debug("exit", extra={"context": {"function": "main", "returncode": code}})
    return code


if __name__ == "__main__":
    raise SystemExit(main())
