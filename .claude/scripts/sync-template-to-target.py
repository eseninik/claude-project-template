"""Mirror this project's .claude/ infrastructure into a target project.

Decisions encoded here (see SESSION-RESUME-CONTEXT-v2.md for the why):

  * MIRROR  — full per-category copy (overwrite differing files, add missing).
  * MERGE   — smart structural merge (settings.json deep-merge, .gitignore line-add).
  * PROTECT — never read, never write. Includes secrets, project-specific session
              data, project source code, and the entire new-project sub-template.

Run order:
  1) python sync-template-to-target.py --tgt "C:/path/to/target"        # dry-run plan
  2) python sync-template-to-target.py --tgt "C:/path/to/target" --apply # do it

Idempotent. Safe to re-run. Never deletes files outside __pycache__.
"""
from __future__ import annotations

import argparse
import filecmp
import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------

MIRROR_DIRS: list[str] = [
    ".claude/scripts",
    ".claude/hooks",
    ".claude/guides",
    ".claude/agents",
    ".claude/commands",
    ".claude/prompts",
    ".claude/schemas",
    ".claude/skills/dual-implement",
    ".claude/ops",
    ".claude/shared/work-templates",
]

# Files inside MIRROR_DIRS that must NEVER be copied (secrets, caches, etc.)
EXCLUDE_NAMES: set[str] = {
    "__pycache__",
    ".env",
    ".env.local",
    ".env.production",
}
EXCLUDE_SUFFIXES: tuple[str, ...] = (".pyc", ".pyo")

# Special-handled files (NOT copied as part of MIRROR_DIRS)
SETTINGS_JSON = ".claude/settings.json"
GITIGNORE = ".gitignore"

# Lines that MUST be present in target .gitignore (added if missing)
GITIGNORE_REQUIRED_LINES: list[str] = [
    ".dual-base-ref",
    ".claude/scheduled_tasks.lock",
    ".claude/tmp/",
    ".claude/logs/",
    ".claude/hooks/.env",
    ".claude/settings.local.json",
    "worktrees/",
]


@dataclass
class Plan:
    new_files: list[tuple[str, str]] = field(default_factory=list)      # (src, tgt)
    changed_files: list[tuple[str, str]] = field(default_factory=list)
    same_files: int = 0
    skipped_files: list[tuple[str, str]] = field(default_factory=list)  # (path, reason)
    settings_action: str = "no-op"
    gitignore_added: list[str] = field(default_factory=list)


def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_NAMES:
        return True
    if path.name in EXCLUDE_NAMES:
        return True
    return path.suffix in EXCLUDE_SUFFIXES


def collect_dir(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    out: list[Path] = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(root)
        if is_excluded(rel):
            continue
        out.append(rel)
    return out


def mirror_category(src_root: Path, tgt_root: Path, rel_dir: str, plan: Plan, apply: bool) -> None:
    src_dir = src_root / rel_dir
    tgt_dir = tgt_root / rel_dir
    if not src_dir.is_dir():
        return
    rels = collect_dir(src_dir)
    for rel in rels:
        s = src_dir / rel
        t = tgt_dir / rel
        rel_display = f"{rel_dir}/{rel.as_posix()}"
        if s.name in EXCLUDE_NAMES:
            plan.skipped_files.append((rel_display, "secret-name"))
            continue
        if t.exists():
            if filecmp.cmp(s, t, shallow=False):
                plan.same_files += 1
                continue
            plan.changed_files.append((str(s), str(t)))
            if apply:
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(s, t)
        else:
            plan.new_files.append((str(s), str(t)))
            if apply:
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(s, t)


def merge_settings(src_root: Path, tgt_root: Path, plan: Plan, apply: bool) -> None:
    s = src_root / SETTINGS_JSON
    t = tgt_root / SETTINGS_JSON
    if not s.is_file():
        return
    if t.is_file() and filecmp.cmp(s, t, shallow=False):
        plan.settings_action = "identical"
        return
    plan.settings_action = "overwrite" if t.exists() else "create"
    if apply:
        json.loads(s.read_text(encoding="utf-8"))
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, t)


def merge_gitignore(tgt_root: Path, plan: Plan, apply: bool) -> None:
    t = tgt_root / GITIGNORE
    existing: list[str] = []
    if t.is_file():
        existing = t.read_text(encoding="utf-8").splitlines()
    existing_set = {line.strip() for line in existing}
    additions: list[str] = []
    for line in GITIGNORE_REQUIRED_LINES:
        if line not in existing_set:
            additions.append(line)
    if not additions:
        return
    plan.gitignore_added = additions
    if apply:
        block = ["", "# Added by template sync 2026-04-26 (Y6-Y17 dual-implement infrastructure)"]
        block.extend(additions)
        new_content = ("\n".join(existing).rstrip() + "\n" + "\n".join(block) + "\n")
        t.write_text(new_content, encoding="utf-8")


def report(plan: Plan, apply: bool) -> None:
    bar = "=" * 70
    print(bar)
    print(f"SYNC {'APPLIED' if apply else 'DRY-RUN PLAN'}")
    print(bar)
    print(f"NEW files       : {len(plan.new_files)}")
    print(f"CHANGED files   : {len(plan.changed_files)}")
    print(f"SAME (unchanged): {plan.same_files}")
    print(f"SKIPPED         : {len(plan.skipped_files)}")
    print(f"settings.json   : {plan.settings_action}")
    print(f".gitignore add  : {len(plan.gitignore_added)} lines")
    if plan.skipped_files:
        print("\nSKIPPED items (not copied):")
        for path, reason in plan.skipped_files:
            print(f"  - {path}  ({reason})")
    if plan.gitignore_added:
        print("\n.gitignore additions:")
        for line in plan.gitignore_added:
            print(f"  + {line}")
    if plan.new_files and not apply:
        print("\nFirst 15 NEW files:")
        for s, t in plan.new_files[:15]:
            rel = os.path.relpath(t, str(Path(t).parents[2]))
            print(f"  + {rel}")
        if len(plan.new_files) > 15:
            print(f"  ... and {len(plan.new_files) - 15} more")
    if plan.changed_files and not apply:
        print("\nFirst 15 CHANGED files:")
        for s, t in plan.changed_files[:15]:
            rel = os.path.relpath(t, str(Path(t).parents[2]))
            print(f"  ~ {rel}")
        if len(plan.changed_files) > 15:
            print(f"  ... and {len(plan.changed_files) - 15} more")
    print(bar)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=".", help="source template project root")
    ap.add_argument("--tgt", required=True, help="target project root")
    ap.add_argument("--apply", action="store_true", help="actually write changes")
    args = ap.parse_args()

    src_root = Path(args.src).resolve()
    tgt_root = Path(args.tgt).resolve()

    if src_root == tgt_root:
        print("ERROR: src and tgt point at the same directory", file=sys.stderr)
        return 2
    if not (src_root / ".claude").is_dir():
        print(f"ERROR: src has no .claude/: {src_root}", file=sys.stderr)
        return 2
    if not tgt_root.is_dir():
        print(f"ERROR: tgt does not exist: {tgt_root}", file=sys.stderr)
        return 2

    plan = Plan()
    for rel in MIRROR_DIRS:
        mirror_category(src_root, tgt_root, rel, plan, args.apply)
    merge_settings(src_root, tgt_root, plan, args.apply)
    merge_gitignore(tgt_root, plan, args.apply)
    report(plan, args.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
