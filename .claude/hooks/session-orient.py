#!/usr/bin/env python3
"""
SessionStart Orientation Hook — reads memory files and outputs context to stdout.
Always exit 0 — never block session start.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

# Force UTF-8 stdout on Windows (avoids charmap codec errors)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def section_active_context(cwd: Path) -> str:
    """Read activeContext.md first 50 lines."""
    ac = cwd / ".claude" / "memory" / "activeContext.md"
    if not ac.exists():
        return ""
    lines = ac.read_text(encoding="utf-8").splitlines()[:50]
    content = "\n".join(lines)
    return f"--- Session Context ---\n{content}\n---"


def load_memory_config(cwd: Path) -> dict:
    """Load memory tier thresholds from ops/config.yaml (simple YAML, stdlib only)."""
    defaults = {"active": 14, "warm": 30, "cold": 90}
    cfg = cwd / ".claude" / "ops" / "config.yaml"
    if not cfg.exists():
        return defaults
    try:
        result, in_mem, in_tiers = dict(defaults), False, False
        for line in cfg.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("memory:"):
                in_mem = True; continue
            if in_mem and not line.startswith((" ", "\t")) and s:
                in_mem = False
            if in_mem and s.startswith("tiers:"):
                in_tiers = True; continue
            if in_tiers and s and ":" in s:
                k, _, v = s.partition(":")
                if k.strip() in defaults:
                    try: result[k.strip()] = int(v.strip())
                    except ValueError: pass
            elif in_tiers and not line.startswith((" ", "\t")) and s:
                in_tiers = False
        return result
    except Exception:
        return defaults


def calc_tier(days: int, th: dict) -> str:
    """Calculate memory tier from days since verification."""
    if days <= th.get("active", 14): return "active"
    if days <= th.get("warm", 30): return "warm"
    if days <= th.get("cold", 90): return "cold"
    return "archive"


def parse_entry_date(header: str) -> date | None:
    """Extract the most recent date from knowledge.md entry header."""
    for pattern in (r"verified:\s*(\d{4}-\d{2}-\d{2})", r"(\d{4}-\d{2}-\d{2})"):
        m = re.search(pattern, header)
        if m:
            try: return date.fromisoformat(m.group(1))
            except ValueError: pass
    return None


def section_knowledge_summary(cwd: Path) -> str:
    """Summarize knowledge.md: count patterns/gotchas with tier labels."""
    km = cwd / ".claude" / "memory" / "knowledge.md"
    if not km.exists():
        return ""
    thresholds = load_memory_config(cwd)
    today = date.today()
    lines = km.read_text(encoding="utf-8").splitlines()
    pattern_titles = []
    gotcha_titles = []
    section = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Patterns"):
            section = "patterns"
        elif stripped.startswith("## Gotchas"):
            section = "gotchas"
        elif stripped.startswith("## ") and section:
            section = None
        elif stripped.startswith("### ") and section:
            title = stripped[4:]  # strip "### "
            entry_date = parse_entry_date(title)
            days = (today - entry_date).days if entry_date else 999
            tier = calc_tier(days, thresholds)
            entry = (title, tier)
            if section == "patterns":
                pattern_titles.append(entry)
            else:
                gotcha_titles.append(entry)
    if not pattern_titles and not gotcha_titles:
        return ""
    tier_counts = {"active": 0, "warm": 0, "cold": 0, "archive": 0}
    for _, tier in pattern_titles + gotcha_titles:
        tier_counts[tier] += 1
    parts = [f"--- Knowledge: {len(pattern_titles)} patterns, {len(gotcha_titles)} gotchas ---"]
    tier_summary = ", ".join(f"{tier_counts[t]} {t}" for t in ("active", "warm", "cold", "archive"))
    parts.append(f"  Tiers: {tier_summary}")
    for title, tier in pattern_titles:
        parts.append(f"  P: [{tier}] {title}")
    for title, tier in gotcha_titles:
        parts.append(f"  G: [{tier}] {title}")
    parts.append("---")
    return "\n".join(parts)


def section_active_pipeline(cwd: Path) -> str:
    """Find the <- CURRENT marker in PIPELINE.md (only on ### Phase: lines)."""
    pl = cwd / "work" / "PIPELINE.md"
    if not pl.exists():
        return ""
    for line in pl.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if "<- CURRENT" in stripped and stripped.startswith("### Phase:"):
            return f"--- Active Pipeline ---\nCurrent phase: {stripped}\n---"
    return ""


def section_observations(cwd: Path) -> str:
    """Count observation .md files and emit alert if needed."""
    obs_dir = cwd / ".claude" / "memory" / "observations"
    if not obs_dir.is_dir():
        return ""
    count = sum(1 for f in obs_dir.iterdir() if f.suffix == ".md")
    if count >= 10:
        return f"WARNING: {count} pending observations -- consider running /rethink"
    if count >= 5:
        return f"NOTE: {count} pending observations"
    return ""


def section_workspace_tree(cwd: Path) -> str:
    """List .md files in project root (depth 1, max 15)."""
    md_files = sorted(f.name for f in cwd.iterdir() if f.is_file() and f.suffix == ".md")[:15]
    if not md_files:
        return ""
    listing = "\n".join(md_files)
    return f"--- Workspace ---\n{listing}\n---"


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)
        cwd = Path(data.get("cwd", ".")).resolve()

        # Vaultguard: only orient inside projects with CLAUDE.md
        if not (cwd / "CLAUDE.md").exists():
            sys.exit(0)

        sections = []

        builders = [
            section_active_context,
            section_knowledge_summary,
            section_active_pipeline,
            section_observations,
            section_workspace_tree,
        ]

        for builder in builders:
            try:
                result = builder(cwd)
                if result:
                    sections.append(result)
            except Exception as e:
                print(f"[session-orient] {builder.__name__} error: {e}", file=sys.stderr)

        if sections:
            print("\n".join(sections))

    except Exception as e:
        print(f"[session-orient] Unexpected error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
    sys.exit(0)
