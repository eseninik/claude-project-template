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
from datetime import datetime, timezone
import filecmp
import json
import logging
import os
import shutil
import subprocess
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

LOCAL_MODIFIED_SKIP_REASON = "LocallyModifiedSkipped"
ROLLBACK_SNAPSHOT_DIR = ".claude/sync-rollback-snapshot"
GIT_TIMEOUT_SECONDS = 30

logger = logging.getLogger(__name__)


@dataclass
class Plan:
    new_files: list[tuple[str, str]] = field(default_factory=list)      # (src, tgt)
    changed_files: list[tuple[str, str]] = field(default_factory=list)
    same_files: int = 0
    skipped_files: list[tuple[str, str]] = field(default_factory=list)  # (path, reason)
    settings_action: str = "no-op"
    gitignore_added: list[str] = field(default_factory=list)
    rollback_snapshot: str | None = None


@dataclass
class RollbackSnapshot:
    tgt_root: Path
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    )
    snapshot_dir: Path | None = None
    captured_files: list[str] = field(default_factory=list)

    def capture(self, target_file: Path, rel_file: str) -> None:
        logger.info(
            "RollbackSnapshot.capture.enter tgt_root=%s rel_file=%s",
            self.tgt_root,
            rel_file,
        )
        if not target_file.exists():
            logger.info(
                "RollbackSnapshot.capture.exit captured=False reason=missing rel_file=%s",
                rel_file,
            )
            return
        if self.snapshot_dir is None:
            self.snapshot_dir = self.tgt_root / ROLLBACK_SNAPSHOT_DIR / self.timestamp
        snapshot_file = self.snapshot_dir / Path(rel_file)
        if snapshot_file.exists():
            logger.info(
                "RollbackSnapshot.capture.exit captured=False reason=already-captured rel_file=%s",
                rel_file,
            )
            return
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target_file, snapshot_file)
        self.captured_files.append(rel_file)
        logger.info(
            "RollbackSnapshot.capture.exit captured=True snapshot_file=%s",
            snapshot_file,
        )


def _target_has_local_changes(tgt_repo: Path, file: Path | str) -> bool:
    logger.info(
        "_target_has_local_changes.enter tgt_repo=%s file=%s",
        tgt_repo,
        file,
    )
    rel_file = Path(file)
    if rel_file.is_absolute():
        try:
            rel_file = rel_file.resolve().relative_to(tgt_repo.resolve())
        except ValueError:
            logger.warning(
                "_target_has_local_changes.exit dirty=False reason=outside-repo file=%s",
                file,
            )
            return False
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(tgt_repo),
                "diff",
                "--quiet",
                "--",
                rel_file.as_posix(),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        logger.exception(
            "_target_has_local_changes.exit dirty=False reason=git-exception file=%s",
            rel_file,
        )
        return False
    dirty = proc.returncode == 1
    if proc.returncode not in (0, 1):
        logger.warning(
            "_target_has_local_changes.exit dirty=False reason=git-returncode returncode=%d stderr=%s",
            proc.returncode,
            proc.stderr.strip(),
        )
        return False
    logger.info("_target_has_local_changes.exit dirty=%s file=%s", dirty, rel_file)
    return dirty


def _should_skip_locally_modified(
    tgt_root: Path,
    target_file: Path,
    rel_display: str,
    plan: Plan,
    force: bool,
) -> bool:
    logger.info(
        "_should_skip_locally_modified.enter rel_display=%s force=%s",
        rel_display,
        force,
    )
    if force:
        logger.info("_should_skip_locally_modified.exit skipped=False reason=force")
        return False
    if _target_has_local_changes(tgt_root, Path(rel_display)):
        plan.skipped_files.append((rel_display, LOCAL_MODIFIED_SKIP_REASON))
        print(
            f"WARNING: skipping locally modified target file: {rel_display}",
            file=sys.stderr,
        )
        logger.warning(
            "_should_skip_locally_modified.exit skipped=True rel_display=%s",
            rel_display,
        )
        return True
    logger.info("_should_skip_locally_modified.exit skipped=False reason=clean")
    return False


def _latest_rollback_snapshot(tgt_root: Path) -> Path | None:
    logger.info("_latest_rollback_snapshot.enter tgt_root=%s", tgt_root)
    snapshot_root = tgt_root / ROLLBACK_SNAPSHOT_DIR
    if not snapshot_root.is_dir():
        logger.info("_latest_rollback_snapshot.exit found=False reason=no-root")
        return None
    snapshots = [path for path in snapshot_root.iterdir() if path.is_dir()]
    if not snapshots:
        logger.info("_latest_rollback_snapshot.exit found=False reason=empty")
        return None
    latest = sorted(snapshots, key=lambda path: path.name)[-1]
    logger.info("_latest_rollback_snapshot.exit found=True latest=%s", latest)
    return latest


def rollback_latest_snapshot(tgt_root: Path) -> Path | None:
    logger.info("rollback_latest_snapshot.enter tgt_root=%s", tgt_root)
    latest = _latest_rollback_snapshot(tgt_root)
    if latest is None:
        logger.info("rollback_latest_snapshot.exit restored=False reason=no-snapshot")
        return None
    restored = 0
    try:
        for snapshot_file in latest.rglob("*"):
            if not snapshot_file.is_file():
                continue
            rel_file = snapshot_file.relative_to(latest)
            target_file = tgt_root / rel_file
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(snapshot_file, target_file)
            restored += 1
    except OSError:
        logger.exception("rollback_latest_snapshot.exit restored=False latest=%s", latest)
        raise
    logger.info(
        "rollback_latest_snapshot.exit restored=True latest=%s files=%d",
        latest,
        restored,
    )
    return latest


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


def mirror_category(
    src_root: Path,
    tgt_root: Path,
    rel_dir: str,
    plan: Plan,
    apply: bool,
    force: bool = False,
    snapshot: RollbackSnapshot | None = None,
) -> None:
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
            if _should_skip_locally_modified(tgt_root, t, rel_display, plan, force):
                continue
            plan.changed_files.append((str(s), str(t)))
            if apply:
                t.parent.mkdir(parents=True, exist_ok=True)
                if snapshot is not None:
                    snapshot.capture(t, rel_display)
                shutil.copy2(s, t)
        else:
            plan.new_files.append((str(s), str(t)))
            if apply:
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(s, t)


def merge_settings(
    src_root: Path,
    tgt_root: Path,
    plan: Plan,
    apply: bool,
    force: bool = False,
    snapshot: RollbackSnapshot | None = None,
) -> None:
    s = src_root / SETTINGS_JSON
    t = tgt_root / SETTINGS_JSON
    if not s.is_file():
        return
    if t.is_file() and filecmp.cmp(s, t, shallow=False):
        plan.settings_action = "identical"
        return
    if t.exists() and _should_skip_locally_modified(tgt_root, t, SETTINGS_JSON, plan, force):
        plan.settings_action = "skipped-local-modified"
        return
    plan.settings_action = "overwrite" if t.exists() else "create"
    if apply:
        json.loads(s.read_text(encoding="utf-8"))
        t.parent.mkdir(parents=True, exist_ok=True)
        if t.exists() and snapshot is not None:
            snapshot.capture(t, SETTINGS_JSON)
        shutil.copy2(s, t)


def merge_gitignore(
    tgt_root: Path,
    plan: Plan,
    apply: bool,
    force: bool = False,
    snapshot: RollbackSnapshot | None = None,
) -> None:
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
    if t.exists() and _should_skip_locally_modified(tgt_root, t, GITIGNORE, plan, force):
        return
    plan.gitignore_added = additions
    if apply:
        if t.exists() and snapshot is not None:
            snapshot.capture(t, GITIGNORE)
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
    if plan.rollback_snapshot:
        print(f"rollback snap   : {plan.rollback_snapshot}")
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
    ap.add_argument("--force", action="store_true", help="overwrite locally modified target files")
    ap.add_argument("--rollback", action="store_true", help="restore the latest pre-sync snapshot")
    args = ap.parse_args()

    src_root = Path(args.src).resolve()
    tgt_root = Path(args.tgt).resolve()

    if not tgt_root.is_dir():
        print(f"ERROR: tgt does not exist: {tgt_root}", file=sys.stderr)
        return 2
    if args.rollback:
        try:
            restored_from = rollback_latest_snapshot(tgt_root)
        except OSError as exc:
            print(f"ERROR: rollback failed: {exc}", file=sys.stderr)
            return 2
        if restored_from is None:
            print(f"ERROR: no rollback snapshot found under {tgt_root / ROLLBACK_SNAPSHOT_DIR}", file=sys.stderr)
            return 1
        print(f"ROLLBACK restored from {restored_from}")
        return 0
    if src_root == tgt_root:
        print("ERROR: src and tgt point at the same directory", file=sys.stderr)
        return 2
    if not (src_root / ".claude").is_dir():
        print(f"ERROR: src has no .claude/: {src_root}", file=sys.stderr)
        return 2

    plan = Plan()
    snapshot = RollbackSnapshot(tgt_root) if args.apply else None
    for rel in MIRROR_DIRS:
        mirror_category(src_root, tgt_root, rel, plan, args.apply, args.force, snapshot)
    merge_settings(src_root, tgt_root, plan, args.apply, args.force, snapshot)
    merge_gitignore(tgt_root, plan, args.apply, args.force, snapshot)
    if snapshot is not None and snapshot.snapshot_dir is not None:
        plan.rollback_snapshot = str(snapshot.snapshot_dir)
    report(plan, args.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
