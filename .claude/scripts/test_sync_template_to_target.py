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
