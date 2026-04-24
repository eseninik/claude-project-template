#!/usr/bin/env python3
"""
SessionStart Orientation Hook — reads memory files and outputs context to stdout.
Always exit 0 — never block session start.
"""

import json
import os
import re
import shutil
import subprocess
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


def codex_warmup(cwd: Path):
    """Launch Codex warm-up in background so first UserPromptSubmit has opinion ready.

    Reads project context, sends it to Codex gpt-5.5 with a generic
    'review project state' prompt. Opinion is written to
    .codex/reviews/parallel-opinion.md — same file that codex-parallel.py uses.
    """
    # Check if codex is available
    codex_bin = shutil.which("codex")
    if not codex_bin:
        npm_codex = Path.home() / "AppData" / "Roaming" / "npm" / "codex.cmd"
        if npm_codex.exists():
            codex_bin = str(npm_codex)
        else:
            return

    reviews_dir = cwd / ".codex" / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    opinion_file = reviews_dir / "parallel-opinion.md"
    prompt_file = reviews_dir / "_prompt.txt"
    params_file = reviews_dir / "_params.json"

    # Build context from project files
    context_parts = []
    claude_md = cwd / "CLAUDE.md"
    if claude_md.exists():
        try:
            context_parts.append(claude_md.read_text(encoding="utf-8")[:300])
        except Exception:
            pass

    ctx_file = cwd / ".claude" / "memory" / "activeContext.md"
    if ctx_file.exists():
        try:
            content = ctx_file.read_text(encoding="utf-8")
            if "## Current Focus" in content:
                context_parts.append(content.split("## Current Focus")[1][:600])
        except Exception:
            pass

    prompt = (
        "Session starting. Review the project state and give 3-5 observations: "
        "potential issues, things to watch out for, or suggestions for the current work. "
        "Be specific to this project.\n\n"
        f"Context:\n{'  '.join(context_parts)}"
    )
    prompt_file.write_text(prompt, encoding="utf-8")

    params = {
        "codex_bin": codex_bin,
        "effort": "low",
        "project_dir": str(cwd),
        "prompt_file": str(prompt_file),
        "opinion_file": str(opinion_file),
        "log_file": str(reviews_dir / "_wrapper.log"),
    }
    params_file.write_text(json.dumps(params, ensure_ascii=False), encoding="utf-8")

    # Use the same wrapper as codex-parallel.py — create if not exists
    wrapper_file = reviews_dir / "_parallel_wrapper.py"
    if not wrapper_file.exists():
        wrapper_file.write_text(r'''#!/usr/bin/env python3
import json, subprocess, sys, pathlib
if sys.platform == "win32":
    for s in [sys.stdin, sys.stdout, sys.stderr]:
        s.reconfigure(encoding="utf-8", errors="replace")
params_path = pathlib.Path(sys.argv[1])
params = json.loads(params_path.read_text(encoding="utf-8"))
prompt = pathlib.Path(params["prompt_file"]).read_text(encoding="utf-8")
opinion_path = pathlib.Path(params["opinion_file"])
log_path = pathlib.Path(params["log_file"])
args = [params["codex_bin"], "exec", "-", "-m", "gpt-5.5",
        "-c", f"reasoning.effort={params['effort']}",
        "--full-auto", "--ephemeral",
        "-o", str(opinion_path)]
try:
    result = subprocess.run(args, input=prompt, stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
        timeout=180, cwd=params["project_dir"])
    if result.returncode != 0:
        log_path.write_text(f"Codex failed (exit {result.returncode})\n{result.stderr[:500]}", encoding="utf-8")
        try: opinion_path.unlink(missing_ok=True)
        except: pass
except subprocess.TimeoutExpired:
    log_path.write_text("Codex timed out", encoding="utf-8")
except Exception as e:
    log_path.write_text(f"Error: {e}", encoding="utf-8")
finally:
    pid_path = pathlib.Path(params["project_dir"]) / ".codex" / "parallel.pid"
    try: pid_path.unlink(missing_ok=True)
    except: pass
''', encoding="utf-8")

    try:
        subprocess.Popen(
            [sys.executable, str(wrapper_file), str(params_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(cwd),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        print("[session-orient] Codex warm-up launched", file=sys.stderr)
    except Exception as e:
        print(f"[session-orient] Codex warm-up failed: {e}", file=sys.stderr)


def main():
    # Hook profile gate
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from hook_base import should_run
        if not should_run("session-orient"):
            sys.exit(0)
    except ImportError:
        pass

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

        # Note: Codex warm-up is handled by codex-parallel.py on first UserPromptSubmit
        # SessionStart Popen gets killed by hook timeout, so warmup here doesn't work

    except Exception as e:
        print(f"[session-orient] Unexpected error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
    sys.exit(0)
