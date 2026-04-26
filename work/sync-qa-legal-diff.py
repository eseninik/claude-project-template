"""One-shot diff helper for sync planning. Compare template .claude/ with QA Legal."""
from __future__ import annotations
import filecmp
import os

SRC_ROOT = r"C:/Bots/Migrator bots/claude-project-template-update"
TGT_ROOT = r"C:/Bots/Migrator bots/QA Legal"

CATEGORIES = [
    ".claude/scripts",
    ".claude/hooks",
    ".claude/guides",
    ".claude/skills",
    ".claude/agents",
    ".claude/commands",
    ".claude/prompts",
    ".claude/schemas",
    ".claude/shared",
    ".claude/ops",
]


def collect(root: str) -> set[str]:
    files: set[str] = set()
    if not os.path.isdir(root):
        return files
    for r, _d, fnames in os.walk(root):
        if "__pycache__" in r:
            continue
        for f in fnames:
            if f.endswith(".pyc"):
                continue
            rel = os.path.relpath(os.path.join(r, f), root).replace(os.sep, "/")
            files.add(rel)
    return files


def main() -> None:
    print("=" * 70)
    print("SYNC PLAN: claude-project-template-update -> QA Legal")
    print("=" * 70)
    grand_only_src = grand_diff = grand_same = 0
    for rel in CATEGORIES:
        s_root = os.path.join(SRC_ROOT, rel)
        t_root = os.path.join(TGT_ROOT, rel)
        s_files = collect(s_root)
        t_files = collect(t_root)
        only_src = sorted(s_files - t_files)
        only_tgt = sorted(t_files - s_files)
        common = s_files & t_files
        diff_files: list[str] = []
        same_files: list[str] = []
        for c in sorted(common):
            sp = os.path.join(s_root, c)
            tp = os.path.join(t_root, c)
            try:
                if filecmp.cmp(sp, tp, shallow=False):
                    same_files.append(c)
                else:
                    diff_files.append(c)
            except OSError:
                diff_files.append(c)
        grand_only_src += len(only_src)
        grand_diff += len(diff_files)
        grand_same += len(same_files)
        print(f"\n## {rel}")
        print(
            f"  src={len(s_files):3d}  tgt={len(t_files):3d}  "
            f"NEW={len(only_src):3d}  CHANGED={len(diff_files):3d}  "
            f"SAME={len(same_files):3d}  ONLY-TGT={len(only_tgt):3d}"
        )
        if only_src:
            print("  NEW (will be added):")
            for f in only_src[:25]:
                print(f"    + {f}")
            if len(only_src) > 25:
                print(f"    ... and {len(only_src) - 25} more")
        if diff_files:
            print("  CHANGED (will be overwritten):")
            for f in diff_files[:15]:
                print(f"    ~ {f}")
            if len(diff_files) > 15:
                print(f"    ... and {len(diff_files) - 15} more")
        if only_tgt:
            print("  ONLY-IN-TARGET (would be left untouched):")
            for f in only_tgt[:8]:
                print(f"    ! {f}")
            if len(only_tgt) > 8:
                print(f"    ... and {len(only_tgt) - 8} more")
    print("\n" + "=" * 70)
    print(f"TOTALS: NEW={grand_only_src}  CHANGED={grand_diff}  SAME={grand_same}")
    print("=" * 70)


if __name__ == "__main__":
    main()
