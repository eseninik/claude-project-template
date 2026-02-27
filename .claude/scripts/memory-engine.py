#!/usr/bin/env python3
"""memory-engine.py -- Memory management for AI agents with Ebbinghaus decay.

Commands: scan init decay touch creative daily stats config knowledge knowledge-touch
Options:  --config <path>  --dry-run  --verbose
"""
import fnmatch, json, os, random, re, subprocess, sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---- defaults ----------------------------------------------------------------
DEFAULT_CONFIG = {
    "tiers": {"active": 14, "warm": 30, "cold": 90},
    "decay_rate": 0.01,
    "relevance_floor": 0.1,
    "skip_patterns": ["_index.md", "MOC-*", ".gitkeep"],
    "type_inference": {"daily/": "daily", "observations/": "observation", "archive/": "archive"},
    "use_git_dates": True,
    "knowledge_path": "knowledge.md",
}
TODAY = date.today()
_FIELD_ORDER = [
    "type", "title", "description", "tags", "priority", "status", "domain",
    "created", "updated", "last_accessed", "date", "relevance", "tier",
]

# ---- YAML frontmatter -------------------------------------------------------
def parse_frontmatter(content: str) -> tuple:
    """Returns (fields, body, had_yaml)."""
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end != -1:
            fields = {}
            for line in content[4:end].split("\n"):
                if ":" in line:
                    k, _, v = line.partition(":")
                    fields[k.strip()] = v.strip()
            return fields, content[end + 5:], True
    return {}, content, False

def build_frontmatter(fields: dict) -> str:
    lines, used = [], set()
    for key in _FIELD_ORDER:
        if key in fields:
            lines.append(f"{key}: {fields[key]}")
            used.add(key)
    for k, v in fields.items():
        if k not in used:
            lines.append(f"{k}: {v}")
    return "---\n" + "\n".join(lines) + "\n---\n"

# ---- date resolution ---------------------------------------------------------
def get_git_date(filepath: Path) -> Optional[date]:
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", str(filepath)],
            capture_output=True, text=True, cwd=str(filepath.parent), timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            return date.fromisoformat(r.stdout.strip()[:10])
    except Exception:
        pass
    return None

def get_best_date(fields: dict, filepath: Path, use_git: bool = True) -> date:
    candidates = []
    for f in ["last_accessed", "updated", "created"]:
        try: candidates.append(date.fromisoformat(fields.get(f, "")[:10]))
        except (ValueError, IndexError): pass
    if use_git:
        gd = get_git_date(filepath)
        if gd: candidates.append(gd)
    if not candidates:
        try: candidates.append(date.fromtimestamp(os.path.getmtime(filepath)))
        except Exception: candidates.append(TODAY)
    return max(candidates)

# ---- core logic --------------------------------------------------------------
def calc_relevance(days: int, rate: float, floor: float) -> float:
    return round(max(floor, 1.0 - days * rate), 2)

def calc_tier(days: int, tiers: dict, current_tier: str = "") -> str:
    if current_tier == "core": return "core"
    for name, thresh in sorted(tiers.items(), key=lambda x: x[1]):
        if days <= thresh: return name
    return "archive"

def infer_type(filepath: Path, type_map: dict) -> str:
    ps = str(filepath).replace("\\", "/")
    for pat, t in type_map.items():
        if pat in ps: return t
    return "note"

def should_skip(filepath: Path, patterns: list) -> bool:
    return any(fnmatch.fnmatch(filepath.name, p) for p in patterns)

def infer_title(body: str) -> str:
    for line in body.split("\n")[:10]:
        if line.startswith("# "): return line[2:].strip()
    return ""

# ---- file I/O (Windows-safe) ------------------------------------------------
def read_file(p: Path) -> str:
    try: return p.read_text(encoding="utf-8", errors="replace")
    except Exception: return ""

def write_file(p: Path, content: str) -> bool:
    try: p.write_text(content, encoding="utf-8"); return True
    except Exception as e:
        print(f"  warning: could not write {p}: {e}", file=sys.stderr); return False

# ---- config ------------------------------------------------------------------
def load_config(target_dir: Path, config_path: str = None) -> dict:
    p = Path(config_path) if config_path else target_dir / ".memory-config.json"
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f: user = json.load(f)
            cfg = {**DEFAULT_CONFIG, **user}
            cfg["tiers"] = {**DEFAULT_CONFIG["tiers"], **user.get("tiers", {})}
            return cfg
        except Exception: pass
    return DEFAULT_CONFIG.copy()

def save_default_config(target_dir: Path):
    p = target_dir / ".memory-config.json"
    try:
        with open(p, "w", encoding="utf-8") as f: json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"  wrote default config: {p}")
    except Exception as e:
        print(f"  error writing config: {e}", file=sys.stderr)

# ---- commands ----------------------------------------------------------------
def find_cards(target_dir: Path, config: dict) -> list:
    return [c for c in sorted(target_dir.rglob("*.md"))
            if c.exists() and not c.is_symlink() and not should_skip(c, config["skip_patterns"])]

def cmd_scan(target_dir: Path, config: dict, verbose: bool = False):
    cards = find_cards(target_dir, config)
    wy, ny, hr, ht, tb = 0, 0, 0, 0, 0
    for card in cards:
        content = read_file(card)
        tb += len(content.encode("utf-8"))
        fields, body, had = parse_frontmatter(content)
        if had: wy += 1
        else: ny += 1
        if "relevance" in fields: hr += 1
        if "tier" in fields: ht += 1
        if verbose and not had: print(f"  no yaml: {card.relative_to(target_dir)}")
    print(f"\n  scan results for {target_dir}:")
    print(f"    total files:     {len(cards)}")
    print(f"    with yaml:       {wy}")
    print(f"    without yaml:    {ny}")
    print(f"    has relevance:   {hr}")
    print(f"    has tier:        {ht}")
    print(f"    total size:      {tb / 1024:.0f} KB")
    print(f"    avg file size:   {tb / max(len(cards), 1) / 1024:.1f} KB")
    if ny: print(f"\n  -> run 'init' to add YAML frontmatter to {ny} files")
    if not hr: print(f"  -> run 'decay' to add relevance scores and tiers")

def cmd_init(target_dir: Path, config: dict, dry_run: bool = False, verbose: bool = False):
    cards = find_cards(target_dir, config)
    added = 0
    for card in cards:
        content = read_file(card)
        fields, body, had = parse_frontmatter(content)
        if had: continue
        nf = {"type": infer_type(card, config["type_inference"])}
        title = infer_title(body)
        if title: nf["title"] = title
        rd = get_best_date({}, card, config["use_git_dates"])
        days = max(0, (TODAY - rd).days)
        nf["last_accessed"] = rd.isoformat()
        nf["relevance"] = str(calc_relevance(days, config["decay_rate"], config["relevance_floor"]))
        nf["tier"] = calc_tier(days, config["tiers"])
        if not dry_run: write_file(card, build_frontmatter(nf) + body)
        added += 1
        if verbose: print(f"  {'[dry] ' if dry_run else ''}init: {card.relative_to(target_dir)} -> {nf['tier']}")
    print(f"\n  {'DRY RUN -- ' if dry_run else ''}init results:")
    print(f"    files processed: {len(cards)}")
    print(f"    frontmatter added: {added}")

def cmd_decay(target_dir: Path, config: dict, dry_run: bool = False, verbose: bool = False):
    cards = find_cards(target_dir, config)
    results = []
    for card in cards:
        content = read_file(card)
        fields, body, had = parse_frontmatter(content)
        rd = get_best_date(fields, card, config["use_git_dates"])
        days = max(0, (TODAY - rd).days)
        old_tier = fields.get("tier", "")
        nr = calc_relevance(days, config["decay_rate"], config["relevance_floor"])
        nt = calc_tier(days, config["tiers"], old_tier)
        if "last_accessed" not in fields: fields["last_accessed"] = rd.isoformat()
        if "type" not in fields: fields["type"] = infer_type(card, config["type_inference"])
        fields["relevance"] = str(nr)
        fields["tier"] = nt
        nc = build_frontmatter(fields) + body
        changed = nc != content
        if changed and not dry_run: write_file(card, nc)
        results.append({"path": str(card.relative_to(target_dir)), "days": days,
                        "relevance": nr, "tier": nt, "changed": changed})
        if verbose and changed:
            print(f"  {'[dry] ' if dry_run else ''}{card.relative_to(target_dir)}: {old_tier or '?'}->{nt} r={nr}")
    tiers = {}
    for r in results: tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
    cc = sum(1 for r in results if r["changed"])
    ar = sum(r["relevance"] for r in results) / max(len(results), 1)
    print(f"\n  {'DRY RUN -- ' if dry_run else ''}decay results:")
    print(f"    total: {len(results)}, changed: {cc}")
    print(f"    avg relevance: {ar:.2f}")
    for t in ["core", "active", "warm", "cold", "archive"]:
        c = tiers.get(t, 0)
        if c: print(f"    {t:8s}: {c:4d} {'#' * (c // 3)}")

def cmd_touch(filepath: str, config: dict):
    """Promote file one tier up (graduated recall)."""
    p = Path(filepath)
    if not p.exists():
        print(f"  error: {filepath} not found"); return
    content = read_file(p)
    fields, body, had = parse_frontmatter(content)
    if fields.get("tier") == "core":
        fields["last_accessed"] = TODAY.isoformat()
        fields["relevance"] = "1.0"
        write_file(p, build_frontmatter(fields) + body)
        print(f"  touched: {filepath} -> core (refreshed)"); return
    tc = config["tiers"]
    ct = fields.get("tier", "archive")
    if ct == "archive":   td, nt = (tc.get("warm", 30) + tc.get("cold", 90)) // 2, "cold"
    elif ct == "cold":    td, nt = (tc.get("active", 14) + tc.get("warm", 30)) // 2, "warm"
    elif ct == "warm":    td, nt = tc.get("active", 14) // 2, "active"
    else:                 td, nt = 0, "active"
    nd = TODAY - timedelta(days=td)
    nr = calc_relevance(td, config["decay_rate"], config["relevance_floor"])
    fields["last_accessed"] = nd.isoformat()
    fields["relevance"] = str(nr)
    fields["tier"] = nt
    write_file(p, build_frontmatter(fields) + body)
    print(f"  touched: {filepath} -> {ct}->{nt}, relevance={nr}")

def cmd_creative(n: int, target_dir: Path, config: dict):
    cards = find_cards(target_dir, config)
    cold = []
    for card in cards:
        content = read_file(card)
        fields, body, _ = parse_frontmatter(content)
        tier = fields.get("tier", "")
        if tier in ("cold", "archive", "warm"):
            cold.append({"path": str(card.relative_to(target_dir)), "tier": tier,
                         "relevance": fields.get("relevance", "?"),
                         "title": fields.get("title", "") or infer_title(body),
                         "last_accessed": fields.get("last_accessed", "?")})
    if not cold:
        print("  no cold/archive cards found -- memory is too fresh"); return
    sample = random.sample(cold, min(n, len(cold)))
    print(f"\n  creative recall -- {len(sample)} random cards:")
    for c in sample:
        print(f"    [{c['tier']}] {c['title'] or c['path']}")
        print(f"           {c['path']} (r={c['relevance']}, last={c['last_accessed']})")
    print(f"\n  read these cards and look for unexpected connections")

def cmd_daily(target_dir: Path, config: dict, dry_run: bool = False, verbose: bool = False):
    dp = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
    files = sorted(f for f in target_dir.rglob("*.md") if dp.match(f.name))
    if not files:
        print(f"  no daily files (YYYY-MM-DD.md) found in {target_dir}"); return
    results = []
    for f in files:
        content = read_file(f)
        fields, body, had = parse_frontmatter(content)
        fd = date.fromisoformat(f.stem)
        days = max(0, (TODAY - fd).days)
        la = fields.get("last_accessed", "")
        try:
            lac = date.fromisoformat(la[:10])
            rd = max(0, (TODAY - max(fd, lac)).days)
        except (ValueError, IndexError): rd = days
        nr = calc_relevance(rd, config["decay_rate"], config["relevance_floor"])
        ot = fields.get("tier", "")
        nt = calc_tier(rd, config["tiers"], ot)
        fields.update({"type": "daily", "date": fd.isoformat(), "relevance": str(nr), "tier": nt})
        if "last_accessed" not in fields: fields["last_accessed"] = fd.isoformat()
        nc = build_frontmatter(fields) + body
        changed = nc != content
        if changed and not dry_run: write_file(f, nc)
        results.append({"file": f.name, "date": fd.isoformat(), "days": rd,
                        "relevance": nr, "tier": nt, "changed": changed})
        if verbose:
            print(f"  {'[dry] ' if dry_run else ''}{f.name}: {ot or '?'}->{nt} r={nr} ({rd}d)")
    tiers = {}
    for r in results: tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
    cc = sum(1 for r in results if r["changed"])
    print(f"\n  {'DRY RUN -- ' if dry_run else ''}daily results:")
    print(f"    files: {len(results)}, changed: {cc}")
    for t in ["active", "warm", "cold", "archive"]:
        c = tiers.get(t, 0)
        if c:
            ds = [r["date"] for r in results if r["tier"] == t]
            print(f"    {t:8s}: {c:3d}  ({ds[0]}..{ds[-1]})")

def cmd_stats(target_dir: Path, config: dict):
    cards = find_cards(target_dir, config)
    tiers, tb, stale, ny = {}, 0, 0, 0
    for card in cards:
        content = read_file(card)
        tb += len(content.encode("utf-8"))
        fields, _, had = parse_frontmatter(content)
        if not had: ny += 1
        t = fields.get("tier", "unknown")
        tiers[t] = tiers.get(t, 0) + 1
        try:
            if (TODAY - date.fromisoformat(fields.get("last_accessed", "")[:10])).days > 90: stale += 1
        except (ValueError, IndexError): pass
    print(f"\n  memory health -- {target_dir}")
    print(f"  {'=' * 40}")
    print(f"  total cards:       {len(cards)}")
    print(f"  total size:        {tb / 1024:.0f} KB")
    print(f"  without yaml:      {ny}")
    print(f"  stale (>90 days):  {stale}")
    print(f"  {'=' * 40}")
    print(f"  tier distribution:")
    for t in ["core", "active", "warm", "cold", "archive", "unknown"]:
        c = tiers.get(t, 0)
        if c:
            pct = c / len(cards) * 100
            print(f"    {t:8s}: {c:4d} ({pct:4.1f}%) {'#' * int(pct / 2)}")
    ab = sum(len(read_file(c).encode("utf-8")) for c in cards
             if parse_frontmatter(read_file(c))[0].get("tier") in ("core", "active"))
    print(f"  {'=' * 40}")
    print(f"  active context:    {ab / 1024:.0f} KB (~{ab // 4:,} tokens)")
    print(f"  total context:     {tb / 1024:.0f} KB (~{tb // 4:,} tokens)")

# ---- knowledge command -------------------------------------------------------
# Matches: ### Name (2026-02-09)
#          ### Name (2026-02-09, verified: 2026-02-09)
#          ### Name (2026-02-13, updated 2026-02-22, verified: 2026-02-22)
#          ### Name (2026-02-09)  last_verified: 2026-02-09
_KH_RE = re.compile(
    r"^###\s+(.+?)\s+\((\d{4}-\d{2}-\d{2})"
    r"(?:,\s*(?:updated\s+\d{4}-\d{2}-\d{2},?\s*)?)?"
    r"(?:,?\s*verified:\s*(\d{4}-\d{2}-\d{2}))?"
    r"\)(?:\s+last_verified:\s*(\d{4}-\d{2}-\d{2}))?\s*$"
)

def _parse_knowledge(content: str) -> list:
    """Parse ### headers with dates into structured entries."""
    entries, lines, cur = [], content.split("\n"), None
    for i, line in enumerate(lines):
        m = _KH_RE.match(line)
        if m:
            if cur: entries.append(cur)
            try: ed = date.fromisoformat(m.group(2))
            except ValueError: ed = TODAY
            lv = None
            for g in (m.group(3), m.group(4)):
                if g:
                    try: lv = date.fromisoformat(g)
                    except ValueError: pass
                    if lv: break
            cur = {"name": m.group(1).strip(), "date": ed, "last_verified": lv,
                   "line_num": i + 1, "body_lines": []}
        elif cur and line.startswith("- "):
            cur["body_lines"].append(line)
        elif cur and line.strip() == "":
            pass  # blank line, keep scanning
        elif cur and line.startswith("### "):
            entries.append(cur); cur = None
    if cur: entries.append(cur)
    return entries

def _resolve_kpath(target_dir: Path, config: dict) -> Path:
    kp = config.get("knowledge_path", "knowledge.md")
    p = target_dir / kp
    if p.exists(): return p
    for c in [target_dir / "knowledge.md", target_dir / ".claude" / "memory" / "knowledge.md"]:
        if c.exists(): return c
    return p

def cmd_knowledge(target_dir: Path, config: dict, dry_run: bool = False, verbose: bool = False):
    """Analyze knowledge.md entries by tier."""
    kp = _resolve_kpath(target_dir, config)
    if not kp.exists():
        print(f"  error: knowledge file not found: {kp}"); return
    content = read_file(kp)
    entries = _parse_knowledge(content)
    if not entries:
        print(f"  no ### entries with (YYYY-MM-DD) found in {kp}"); return
    ts, results, modified, lines = {}, [], False, content.split("\n")
    for e in entries:
        rd = e["last_verified"] or e["date"]
        days = max(0, (TODAY - rd).days)
        rel = calc_relevance(days, config["decay_rate"], config["relevance_floor"])
        tier = calc_tier(days, config["tiers"])
        ts[tier] = ts.get(tier, 0) + 1
        results.append({"name": e["name"], "date": e["date"].isoformat(),
                        "last_verified": e["last_verified"].isoformat() if e["last_verified"] else None,
                        "days": days, "relevance": rel, "tier": tier, "line": e["line_num"],
                        "bullets": len(e["body_lines"])})
        # Add verified date inside parens if completely missing
        if e["last_verified"] is None:
            ol = lines[e["line_num"] - 1]
            if "verified:" not in ol and "last_verified:" not in ol:
                nl = re.sub(r"\)(\s*)$", f", verified: {e['date'].isoformat()})\\1", ol.rstrip())
                if ol.rstrip() != nl:
                    lines[e["line_num"] - 1] = nl; modified = True
        if verbose:
            vs = f", verified={e['last_verified']}" if e["last_verified"] else ""
            print(f"  [{tier:7s}] {e['name']} (date={e['date']}{vs}, {days}d, r={rel:.2f})")
    if modified and not dry_run: write_file(kp, "\n".join(lines))
    print(f"\n  {'DRY RUN -- ' if dry_run else ''}knowledge analysis -- {kp.name}")
    print(f"    entries: {len(entries)}")
    av = sum(1 for r in results if r["last_verified"] is None)
    if av: print(f"    verified dates added: {av}")
    print(f"    tier distribution:")
    for t in ["active", "warm", "cold", "archive"]:
        c = ts.get(t, 0)
        if c:
            names = [r["name"] for r in results if r["tier"] == t]
            preview = ", ".join(names[:3]) + (f", +{len(names)-3} more" if len(names) > 3 else "")
            print(f"      {t:8s}: {c:3d}  ({preview})")
    ac = ts.get("archive", 0)
    if ac: print(f"\n  -> {ac} entries are archive-tier -- consider pruning or verifying")
    cc = ts.get("cold", 0)
    if cc: print(f"  -> {cc} entries are cold -- 'knowledge-touch <name>' to refresh")

def cmd_knowledge_touch(name_query: str, target_dir: Path, config: dict,
                        dry_run: bool = False, verbose: bool = False):
    """Touch a knowledge.md entry: update date to today if >7 days old."""
    kp = _resolve_kpath(target_dir, config)
    if not kp.exists():
        print(f"  error: knowledge file not found: {kp}"); return
    content = read_file(kp)
    entries = _parse_knowledge(content)
    ql = name_query.lower()
    matches = [e for e in entries if ql in e["name"].lower()]
    if not matches:
        print(f"  error: no entry matching '{name_query}' found")
        print(f"  available entries:")
        for e in entries[:10]: print(f"    - {e['name']} ({e['date']})")
        if len(entries) > 10: print(f"    ... and {len(entries)-10} more")
        return
    if len(matches) > 1:
        print(f"  multiple matches for '{name_query}':")
        for e in matches: print(f"    - {e['name']} ({e['date']})")
        print(f"  please be more specific"); return
    entry = matches[0]
    rd = entry["last_verified"] or entry["date"]
    ds = max(0, (TODAY - rd).days)
    if ds <= 7:
        print(f"  skip: '{entry['name']}' was verified {ds} days ago (threshold: 7)")
        print(f"  no update needed -- entry is still fresh"); return
    lines = content.split("\n")
    li = entry["line_num"] - 1
    nds = TODAY.isoformat()
    # Replace entire parenthesized block
    nl = re.sub(r"\([^)]+\)", f"({nds}, verified: {nds})", lines[li], count=1)
    # Update trailing last_verified if present
    if "last_verified:" in nl:
        parts = nl.split(")")
        if len(parts) > 1 and "last_verified:" in parts[-1]:
            parts[-1] = re.sub(r"last_verified:\s*\d{4}-\d{2}-\d{2}", f"last_verified: {nds}", parts[-1])
            nl = ")".join(parts)
    lines[li] = nl
    if not dry_run: write_file(kp, "\n".join(lines))
    nt = calc_tier(0, config["tiers"])
    print(f"  {'[dry] ' if dry_run else ''}touched: '{entry['name']}' ({rd} -> {nds}, {ds}d old)")
    print(f"    tier: {calc_tier(ds, config['tiers'])} -> {nt}, relevance: 1.0")

# ---- main -------------------------------------------------------------------
def main():
    try: _main_inner()
    except Exception as e:
        print(f"  error: {e}", file=sys.stderr); sys.exit(0)

def _main_inner():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    cmd = args[0]
    dry_run = "--dry-run" in args
    verbose = "--verbose" in args
    config_path = None
    if "--config" in args:
        idx = args.index("--config")
        config_path = args[idx + 1] if idx + 1 < len(args) else None
    target = None
    for a in args[1:]:
        if not a.startswith("-") and a != config_path: target = a; break

    if cmd == "touch":
        if not target: print("  error: touch requires a file path"); return
        cmd_touch(target, load_config(Path(target).parent, config_path)); return

    if cmd == "creative":
        n, cdir = 5, None
        for a in args[1:]:
            if not a.startswith("-"):
                try: n = int(a)
                except ValueError: cdir = a
        td = Path(cdir) if cdir else Path(".")
        cmd_creative(n, td, load_config(td, config_path)); return

    if cmd == "knowledge-touch":
        if not target:
            print("  error: knowledge-touch requires a pattern name"); return
        edir, found = None, False
        for a in args[1:]:
            if not a.startswith("-") and a != config_path:
                if not found: found = True
                else: edir = a; break
        td = Path(edir) if edir else Path(".")
        cmd_knowledge_touch(target, td, load_config(td, config_path), dry_run, verbose); return

    td = Path(target) if target else Path(".")
    # If target is a file, use its parent as dir (useful for: knowledge path/to/knowledge.md)
    if td.is_file():
        cfg = load_config(td.parent, config_path)
        cfg["knowledge_path"] = td.name
        td = td.parent
    elif td.is_dir():
        cfg = load_config(td, config_path)
    else:
        print(f"  error: {td} is not a file or directory"); return
    cmds = {"scan": lambda: cmd_scan(td, cfg, verbose),
            "init": lambda: cmd_init(td, cfg, dry_run, verbose),
            "decay": lambda: cmd_decay(td, cfg, dry_run, verbose),
            "daily": lambda: cmd_daily(td, cfg, dry_run, verbose),
            "stats": lambda: cmd_stats(td, cfg),
            "config": lambda: save_default_config(td),
            "knowledge": lambda: cmd_knowledge(td, cfg, dry_run, verbose)}
    if cmd in cmds: cmds[cmd]()
    else:
        print(f"  unknown command: {cmd}")
        print("  commands: scan init decay daily touch creative stats config knowledge knowledge-touch")

if __name__ == "__main__":
    main()
