"""Tests for sync-template-to-target.py conflict guard and rollback."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("sync-template-to-target.py")
SPEC = importlib.util.spec_from_file_location("sync_template_to_target", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Cannot load {SCRIPT_PATH}")
sync = importlib.util.module_from_spec(SPEC)
sys.modules["sync_template_to_target"] = sync
SPEC.loader.exec_module(sync)

REL_FILE = ".claude/scripts/example.py"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    return proc


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_sync_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    src = tmp_path / "src"
    tgt = tmp_path / "tgt"
    _write(src / REL_FILE, "template\n")
    _write(tgt / REL_FILE, "target\n")
    _git(tgt, "init", "-q")
    _git(tgt, "config", "user.email", "test@example.invalid")
    _git(tgt, "config", "user.name", "Test User")
    _git(tgt, "add", REL_FILE)
    _git(tgt, "commit", "-q", "-m", "initial")
    return src, tgt, tgt / REL_FILE


def _apply_scripts_sync(src: Path, tgt: Path, force: bool) -> tuple[object, object]:
    plan = sync.Plan()
    snapshot = sync.RollbackSnapshot(tgt)
    sync.mirror_category(
        src,
        tgt,
        ".claude/scripts",
        plan,
        apply=True,
        force=force,
        snapshot=snapshot,
    )
    return plan, snapshot


def test_sync_skips_locally_modified_without_force(tmp_path: Path) -> None:
    src, tgt, target_file = _make_sync_fixture(tmp_path)
    target_file.write_text("local change\n", encoding="utf-8")

    plan, snapshot = _apply_scripts_sync(src, tgt, force=False)

    assert target_file.read_text(encoding="utf-8") == "local change\n"
    assert (REL_FILE, sync.LOCAL_MODIFIED_SKIP_REASON) in plan.skipped_files
    assert plan.changed_files == []
    assert snapshot.snapshot_dir is None


def test_sync_overwrites_locally_modified_with_force(tmp_path: Path) -> None:
    src, tgt, target_file = _make_sync_fixture(tmp_path)
    target_file.write_text("local change\n", encoding="utf-8")

    plan, snapshot = _apply_scripts_sync(src, tgt, force=True)

    assert target_file.read_text(encoding="utf-8") == "template\n"
    assert plan.skipped_files == []
    assert len(plan.changed_files) == 1
    assert snapshot.snapshot_dir is not None
    assert (snapshot.snapshot_dir / REL_FILE).read_text(encoding="utf-8") == "local change\n"


def test_sync_normal_overwrite_when_target_clean(tmp_path: Path) -> None:
    src, tgt, target_file = _make_sync_fixture(tmp_path)

    plan, snapshot = _apply_scripts_sync(src, tgt, force=False)

    assert target_file.read_text(encoding="utf-8") == "template\n"
    assert plan.skipped_files == []
    assert len(plan.changed_files) == 1
    assert snapshot.snapshot_dir is not None


def test_sync_creates_rollback_snapshot(tmp_path: Path) -> None:
    src, tgt, _target_file = _make_sync_fixture(tmp_path)

    _plan, snapshot = _apply_scripts_sync(src, tgt, force=False)

    assert snapshot.snapshot_dir is not None
    snapshot_file = snapshot.snapshot_dir / REL_FILE
    assert snapshot_file.is_file()
    assert snapshot_file.read_text(encoding="utf-8") == "target\n"


def test_rollback_restores_pre_sync_state(tmp_path: Path) -> None:
    src, tgt, target_file = _make_sync_fixture(tmp_path)
    _plan, snapshot = _apply_scripts_sync(src, tgt, force=False)
    assert target_file.read_text(encoding="utf-8") == "template\n"

    restored_from = sync.rollback_latest_snapshot(tgt)

    assert restored_from == snapshot.snapshot_dir
    assert target_file.read_text(encoding="utf-8") == "target\n"

# ---------------------------------------------------------------------------
# Z33 вЂ” MIRROR_TOP_FILES (full QA-Legal parity)
# ---------------------------------------------------------------------------

TOP_FILES_EXPECTED = (
    ".github/workflows/dual-implement-ci.yml",
    "CHANGELOG.md",
    "mypy.ini",
)


def _make_top_files_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Build a synthetic src/tgt with all three top-level files in src.

    Target is initialized as a git repo (existing helper requires it for the
    locally-modified guard via `git diff --quiet`). Existing top files in
    target are committed first so subsequent local edits register as dirty.
    """
    src = tmp_path / "src"
    tgt = tmp_path / "tgt"
    # Source content for all three files.
    _write(src / ".github/workflows/dual-implement-ci.yml", "name: dual\nversion: 1\n")
    _write(src / "CHANGELOG.md", "# Changelog\n\n## v1\n")
    _write(src / "mypy.ini", "[mypy]\nstrict = True\n")
    # Ensure src has a .claude/ marker (required by main()) вЂ” irrelevant for
    # direct mirror_top_file calls but kept for completeness.
    _write(src / ".claude/ops/.gitkeep", "")
    # Target: initialize and commit baseline (older versions of top files) so
    # tests can simulate "locally modified" state.
    _write(tgt / ".github/workflows/dual-implement-ci.yml", "name: old\n")
    _write(tgt / "CHANGELOG.md", "# old\n")
    _write(tgt / "mypy.ini", "[mypy]\n")
    _git(tgt, "init", "-q")
    _git(tgt, "config", "user.email", "test@example.invalid")
    _git(tgt, "config", "user.name", "Test User")
    _git(tgt, "add", ".github/workflows/dual-implement-ci.yml", "CHANGELOG.md", "mypy.ini")
    _git(tgt, "commit", "-q", "-m", "initial-top-files")
    return src, tgt


def test_mirror_top_files_constant_lists_three_files() -> None:
    """AC-1: MIRROR_TOP_FILES contains exactly the three Round-8 files."""
    assert tuple(sync.MIRROR_TOP_FILES) == TOP_FILES_EXPECTED


def test_sync_mirrors_top_level_dual_implement_ci_yml(tmp_path: Path) -> None:
    """AC-2: top-level CI workflow file is mirrored from src into tgt."""
    src, tgt = _make_top_files_fixture(tmp_path)
    plan = sync.Plan()
    snapshot = sync.RollbackSnapshot(tgt)

    sync.mirror_top_file(
        src,
        tgt,
        ".github/workflows/dual-implement-ci.yml",
        plan,
        apply=True,
        force=False,
        snapshot=snapshot,
    )

    target_file = tgt / ".github/workflows/dual-implement-ci.yml"
    assert target_file.read_text(encoding="utf-8") == "name: dual\nversion: 1\n"
    assert plan.skipped_files == []
    assert len(plan.changed_files) == 1
    # Snapshot of pre-sync target captured for rollback.
    assert snapshot.snapshot_dir is not None
    snap_file = snapshot.snapshot_dir / ".github/workflows/dual-implement-ci.yml"
    assert snap_file.read_text(encoding="utf-8") == "name: old\n"


def test_sync_mirrors_top_level_changelog_and_mypy_ini(tmp_path: Path) -> None:
    """AC-3: CHANGELOG.md and mypy.ini are mirrored end-to-end via main loop."""
    src, tgt = _make_top_files_fixture(tmp_path)
    plan = sync.Plan()
    snapshot = sync.RollbackSnapshot(tgt)

    for top in sync.MIRROR_TOP_FILES:
        sync.mirror_top_file(src, tgt, top, plan, apply=True, force=False, snapshot=snapshot)

    assert (tgt / "CHANGELOG.md").read_text(encoding="utf-8") == "# Changelog\n\n## v1\n"
    assert (tgt / "mypy.ini").read_text(encoding="utf-8") == "[mypy]\nstrict = True\n"
    # All three top files changed (clean target, none locally modified).
    assert len(plan.changed_files) == 3
    assert plan.skipped_files == []


def test_top_files_skipped_when_locally_modified_without_force(tmp_path: Path) -> None:
    """AC-4: locally modified top files are skipped without --force, and ARE
    overwritten with --force (rollback snapshot captured)."""
    src, tgt = _make_top_files_fixture(tmp_path)
    # Locally modify CHANGELOG.md (uncommitted edit).
    (tgt / "CHANGELOG.md").write_text("# locally edited\n", encoding="utf-8")

    # Without --force: skipped.
    plan_skip = sync.Plan()
    sync.mirror_top_file(
        src,
        tgt,
        "CHANGELOG.md",
        plan_skip,
        apply=True,
        force=False,
        snapshot=sync.RollbackSnapshot(tgt),
    )
    assert (tgt / "CHANGELOG.md").read_text(encoding="utf-8") == "# locally edited\n"
    assert ("CHANGELOG.md", sync.LOCAL_MODIFIED_SKIP_REASON) in plan_skip.skipped_files
    assert plan_skip.changed_files == []

    # With --force: overwritten and snapshotted.
    plan_force = sync.Plan()
    snapshot_force = sync.RollbackSnapshot(tgt)
    sync.mirror_top_file(
        src,
        tgt,
        "CHANGELOG.md",
        plan_force,
        apply=True,
        force=True,
        snapshot=snapshot_force,
    )
    assert (tgt / "CHANGELOG.md").read_text(encoding="utf-8") == "# Changelog\n\n## v1\n"
    assert plan_force.skipped_files == []
    assert len(plan_force.changed_files) == 1
    assert snapshot_force.snapshot_dir is not None
    assert (snapshot_force.snapshot_dir / "CHANGELOG.md").read_text(encoding="utf-8") == "# locally edited\n"
