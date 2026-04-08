#!/usr/bin/env python3
"""
context-layers.py -- 4-Layer Context Loading for Claude Code Templates
=====================================================================

Adapted from MemPalace's 4-layer memory stack (mempalace/layers.py).
Loads project context in graduated layers to minimize token usage.

    Layer 0: Identity       (~50 tokens)    -- Always loaded. Project name + key info from CLAUDE.md
    Layer 1: Active Patterns (~300 tokens)   -- Always loaded. Active-tier entries from knowledge.md
    Layer 2: Session Context (~200-500)      -- Always loaded. Current focus from activeContext.md
    Layer 3: Deep Search    (on demand)      -- grep-based retrieval from all memory files

Wake-up cost: ~550-850 tokens (L0+L1+L2). Was ~2-5K with full file load.
Savings: ~70-84%.

CLI:
    py -3 .claude/scripts/context-layers.py wake-up          # L0+L1+L2 combined
    py -3 .claude/scripts/context-layers.py l0               # Identity only
    py -3 .claude/scripts/context-layers.py l1               # Active patterns only
    py -3 .claude/scripts/context-layers.py l2               # Session context only
    py -3 .claude/scripts/context-layers.py l3 "query here"  # Deep search
    py -3 .claude/scripts/context-layers.py stats            # Token counts per layer
"""

import logging
import os
import re
import sys
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logger = logging.getLogger("context-layers")
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG if os.environ.get("DEBUG") else logging.WARNING)


def _token_estimate(text):
    """Estimate token count. ~4 chars per token (MemPalace heuristic)."""
    return len(text) // 4


# ---------------------------------------------------------------------------
# Layer 0 -- Project Identity
# ---------------------------------------------------------------------------


class Layer0:
    """
    ~50 tokens. Always loaded.
    Reads the first 5 lines of CLAUDE.md for project name, description, branch.
    Minimal footprint -- just enough to orient the agent.
    """

    HEADER_LINES = 5

    def __init__(self, project_root):
        self.claude_md = os.path.join(project_root, "CLAUDE.md")
        self._text = None
        logger.debug("Layer0 init: claude_md=%s", self.claude_md)

    def render(self):
        """Return project identity text from CLAUDE.md header."""
        if self._text is not None:
            return self._text

        logger.debug("Layer0 render: reading %s", self.claude_md)
        if os.path.exists(self.claude_md):
            try:
                with open(self.claude_md, "r", encoding="utf-8") as f:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= self.HEADER_LINES:
                            break
                        lines.append(line.rstrip())
                # Strip empty trailing lines
                while lines and not lines[-1].strip():
                    lines.pop()
                self._text = "\n".join(lines)
                logger.debug("Layer0 render: loaded %d lines, %d chars", len(lines), len(self._text))
            except Exception as exc:
                logger.error("Layer0 render: failed to read CLAUDE.md: %s", exc)
                self._text = "## L0 -- IDENTITY\nCLAUDE.md read error"
        else:
            logger.warning("Layer0 render: CLAUDE.md not found at %s", self.claude_md)
            self._text = "## L0 -- IDENTITY\nNo CLAUDE.md found. Create one in project root."

        return self._text

    def token_estimate(self):
        return _token_estimate(self.render())


# ---------------------------------------------------------------------------
# Layer 1 -- Active Patterns (filtered from knowledge.md)
# ---------------------------------------------------------------------------


class Layer1:
    """
    ~300 tokens. Always loaded.
    Reads knowledge.md, filters ONLY entries with tier 'active' (verified within 14 days).
    Formats as compact one-liners. Caps at MAX_CHARS (~300 tokens).
    """

    MAX_CHARS = 1200  # ~300 tokens
    ACTIVE_DAYS = 14  # entries verified within this many days = active tier

    def __init__(self, project_root):
        self.knowledge_path = os.path.join(project_root, ".claude", "memory", "knowledge.md")
        logger.debug("Layer1 init: knowledge_path=%s", self.knowledge_path)

    def generate(self):
        """Parse knowledge.md, extract active-tier entries, format as compact list."""
        logger.debug("Layer1 generate: reading %s", self.knowledge_path)

        if not os.path.exists(self.knowledge_path):
            logger.warning("Layer1 generate: knowledge.md not found")
            return "## L1 -- ACTIVE PATTERNS (0 patterns, ~0 tokens)\nNo knowledge.md found."

        try:
            with open(self.knowledge_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as exc:
            logger.error("Layer1 generate: failed to read knowledge.md: %s", exc)
            return "## L1 -- ACTIVE PATTERNS\nRead error."

        # Parse entries: ### Name (date, verified: date)
        cutoff = datetime.now() - timedelta(days=self.ACTIVE_DAYS)
        pattern = re.compile(
            r"^### (.+?)\s*\(.*?verified:\s*(\d{4}-\d{2}-\d{2})\)",
            re.MULTILINE,
        )

        entries = []
        for match in pattern.finditer(content):
            name = match.group(1).strip()
            verified_str = match.group(2)
            try:
                verified_date = datetime.strptime(verified_str, "%Y-%m-%d")
            except ValueError:
                logger.warning("Layer1 generate: bad date for entry '%s'", name)
                continue

            if verified_date >= cutoff:
                # Extract the first bullet point after this heading as the key point
                start_pos = match.end()
                key_point = self._extract_first_bullet(content, start_pos)
                entries.append((name, key_point, verified_date))

        logger.debug("Layer1 generate: found %d active entries", len(entries))

        if not entries:
            msg = "## L1 -- ACTIVE PATTERNS (0 patterns, ~0 tokens)\n"
            msg += "No active patterns (all older than %d days)." % self.ACTIVE_DAYS
            return msg

        # Sort by most recently verified first
        entries.sort(key=lambda e: e[2], reverse=True)

        # Build compact output, respecting MAX_CHARS
        lines = []
        total_len = 0
        for name, key_point, _ in entries:
            if key_point:
                line = "- %s: %s" % (name, key_point)
            else:
                line = "- %s" % name
            if total_len + len(line) > self.MAX_CHARS:
                lines.append("- ... (more in L3 search)")
                break
            lines.append(line)
            total_len += len(line) + 1  # +1 for newline

        body = "\n".join(lines)
        token_est = _token_estimate(body)
        header = "## L1 -- ACTIVE PATTERNS (%d patterns, ~%d tokens)" % (len(entries), token_est)

        result = header + "\n" + body
        logger.debug("Layer1 generate: output %d chars, ~%d tokens", len(result), _token_estimate(result))
        return result

    @staticmethod
    def _extract_first_bullet(content, start_pos):
        """Extract the text of the first bullet point after a given position."""
        remaining = content[start_pos:]
        for line in remaining.split("\n"):
            stripped = line.strip()
            if stripped.startswith("- ") and len(stripped) > 4:
                point = stripped[2:].strip()
                # Truncate long points
                if len(point) > 120:
                    point = point[:117] + "..."
                return point
            # Stop at next heading
            if stripped.startswith("###"):
                break
        return ""

    def token_estimate(self):
        return _token_estimate(self.generate())

    def count_active(self):
        """Count active entries without generating full output."""
        if not os.path.exists(self.knowledge_path):
            return 0
        try:
            with open(self.knowledge_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return 0

        cutoff = datetime.now() - timedelta(days=self.ACTIVE_DAYS)
        pattern = re.compile(
            r"^### .+?\(.*?verified:\s*(\d{4}-\d{2}-\d{2})\)",
            re.MULTILINE,
        )
        count = 0
        for match in pattern.finditer(content):
            try:
                verified = datetime.strptime(match.group(1), "%Y-%m-%d")
                if verified >= cutoff:
                    count += 1
            except ValueError:
                continue
        return count


# ---------------------------------------------------------------------------
# Layer 2 -- Session Context (current focus from activeContext.md)
# ---------------------------------------------------------------------------


class Layer2:
    """
    ~200-500 tokens. Always loaded at wake-up.
    Reads activeContext.md, extracts ONLY the Current Focus section (first ## block).
    Skips historical sections to keep it compact.
    """

    MAX_CHARS = 2000  # ~500 tokens hard cap

    def __init__(self, project_root):
        self.context_path = os.path.join(project_root, ".claude", "memory", "activeContext.md")
        logger.debug("Layer2 init: context_path=%s", self.context_path)

    def render(self):
        """Extract the Current Focus section from activeContext.md."""
        logger.debug("Layer2 render: reading %s", self.context_path)

        if not os.path.exists(self.context_path):
            logger.warning("Layer2 render: activeContext.md not found")
            return "## L2 -- CURRENT SESSION\nNo activeContext.md found."

        try:
            with open(self.context_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as exc:
            logger.error("Layer2 render: failed to read activeContext.md: %s", exc)
            return "## L2 -- CURRENT SESSION\nRead error."

        # Extract the first ## section (Current Focus)
        focus_text = self._extract_first_section(content)

        if not focus_text:
            logger.debug("Layer2 render: no Current Focus section found, using header")
            # Fall back to first 500 chars
            focus_text = content[:500]
            if len(content) > 500:
                focus_text += "\n... (truncated)"

        # Cap at MAX_CHARS to keep L2 compact
        if len(focus_text) > self.MAX_CHARS:
            focus_text = focus_text[:self.MAX_CHARS] + "\n... (truncated, use L3 for full search)"

        result = "## L2 -- CURRENT SESSION\n" + focus_text
        logger.debug("Layer2 render: output %d chars, ~%d tokens", len(result), _token_estimate(result))
        return result

    @staticmethod
    def _extract_first_section(content):
        """Extract content from the first ## heading to the next ## heading."""
        lines = content.split("\n")
        in_section = False
        section_lines = []

        for line in lines:
            if line.startswith("## ") and not in_section:
                in_section = True
                section_lines.append(line)
                continue
            if line.startswith("## ") and in_section:
                # Hit the next section -- stop
                break
            if in_section:
                section_lines.append(line)

        # Strip trailing empty lines
        while section_lines and not section_lines[-1].strip():
            section_lines.pop()

        return "\n".join(section_lines) if section_lines else ""

    def token_estimate(self):
        return _token_estimate(self.render())


# ---------------------------------------------------------------------------
# Layer 3 -- Deep Search (grep-based fallback)
# ---------------------------------------------------------------------------


class Layer3:
    """
    Unlimited depth. On-demand search across all memory files.
    Uses grep-based search (no ChromaDB dependency).
    Falls back to memory-engine.py if available.
    """

    SEARCH_DIRS = [
        os.path.join(".claude", "memory"),
        os.path.join(".claude", "adr"),
    ]

    def __init__(self, project_root):
        self.project_root = project_root
        self.memory_engine = os.path.join(project_root, ".claude", "scripts", "memory-engine.py")
        logger.debug("Layer3 init: project_root=%s", self.project_root)

    def search(self, query, max_results=10):
        """
        Search memory files for a query string.
        Uses grep-based approach -- finds lines containing query terms.
        """
        logger.debug("Layer3 search: query='%s', max_results=%d", query, max_results)

        if not query.strip():
            return "## L3 -- DEEP SEARCH\nNo query provided."

        # Collect all .md files from search directories
        md_files = []
        for search_dir in self.SEARCH_DIRS:
            full_dir = os.path.join(self.project_root, search_dir)
            if os.path.isdir(full_dir):
                for root, _dirs, files in os.walk(full_dir):
                    for fname in files:
                        if fname.endswith(".md"):
                            md_files.append(os.path.join(root, fname))

        if not md_files:
            logger.warning("Layer3 search: no .md files found in search dirs")
            return "## L3 -- DEEP SEARCH\nNo memory files found."

        # Split query into terms for matching
        terms = [t.lower() for t in query.split() if len(t) > 2]
        if not terms:
            terms = [query.lower().strip()]

        logger.debug("Layer3 search: searching %d files for terms=%s", len(md_files), terms)

        # Score each line by number of matching terms
        hits = []
        for fpath in md_files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        lower_line = line.lower()
                        score = sum(1 for t in terms if t in lower_line)
                        if score > 0:
                            rel_path = os.path.relpath(fpath, self.project_root)
                            hits.append((score, rel_path, line_num, line.strip()))
            except Exception as exc:
                logger.warning("Layer3 search: error reading %s: %s", fpath, exc)
                continue

        # Sort by score descending, take top N
        hits.sort(key=lambda x: x[0], reverse=True)
        top_hits = hits[:max_results]

        if not top_hits:
            return "## L3 -- DEEP SEARCH for \"%s\"\nNo results found." % query

        header = "## L3 -- DEEP SEARCH for \"%s\" (%d total matches, showing top %d)" % (
            query, len(hits), len(top_hits)
        )
        lines = [header]
        for score, rel_path, line_num, text in top_hits:
            # Truncate long lines
            display = text if len(text) <= 200 else text[:197] + "..."
            lines.append("  [%d/%d] %s:%d" % (score, len(terms), rel_path, line_num))
            lines.append("      %s" % display)

        result = "\n".join(lines)
        logger.debug("Layer3 search: found %d total hits, returning %d", len(hits), len(top_hits))
        return result

    def has_chromadb(self):
        """Check if ChromaDB + semantic-search.py is available."""
        semantic_search = os.path.join(self.project_root, ".claude", "scripts", "semantic-search.py")
        if not os.path.exists(semantic_search):
            return False
        try:
            import importlib
            importlib.import_module("chromadb")
            return True
        except ImportError:
            return False


# ---------------------------------------------------------------------------
# ContextStack -- unified interface (mirrors MemPalace MemoryStack)
# ---------------------------------------------------------------------------


class ContextStack:
    """
    The full 4-layer context stack. Adapted from MemPalace MemoryStack.

        stack = ContextStack("/path/to/project")
        print(stack.wake_up())                # L0+L1+L2 (~550-850 tokens)
        print(stack.search("pipeline"))        # L3 deep search
        print(stack.stats())                   # Token counts per layer
    """

    def __init__(self, project_root):
        self.project_root = project_root
        self.l0 = Layer0(project_root)
        self.l1 = Layer1(project_root)
        self.l2 = Layer2(project_root)
        self.l3 = Layer3(project_root)
        logger.debug("ContextStack init: project_root=%s", project_root)

    def wake_up(self):
        """
        Generate wake-up text: L0 (identity) + L1 (active patterns) + L2 (session context).
        Typically ~550-850 tokens. Inject into system prompt or first message.
        """
        logger.info("ContextStack wake_up: generating L0+L1+L2")
        parts = []

        # L0: Project Identity
        parts.append("## L0 -- PROJECT IDENTITY")
        parts.append(self.l0.render())
        parts.append("")

        # L1: Active Patterns
        parts.append(self.l1.generate())
        parts.append("")

        # L2: Session Context
        parts.append(self.l2.render())

        result = "\n".join(parts)
        logger.info("ContextStack wake_up: total %d chars, ~%d tokens", len(result), _token_estimate(result))
        return result

    def search(self, query, max_results=10):
        """Deep L3 search across all memory files."""
        logger.info("ContextStack search: query='%s'", query)
        return self.l3.search(query, max_results=max_results)

    def stats(self):
        """Token counts and status per layer."""
        logger.info("ContextStack stats: computing")

        l0_text = self.l0.render()
        l1_text = self.l1.generate()
        l2_text = self.l2.render()

        l0_tokens = _token_estimate(l0_text)
        l1_tokens = _token_estimate(l1_text)
        l2_tokens = _token_estimate(l2_text)
        active_count = self.l1.count_active()
        has_chromadb = self.l3.has_chromadb()

        wake_total = l0_tokens + l1_tokens + l2_tokens

        # Estimate what full load would cost
        full_load = self._estimate_full_load()
        if full_load > 0:
            savings_pct = int((1 - wake_total / full_load) * 100)
        else:
            savings_pct = 0

        chromadb_status = "installed" if has_chromadb else "not installed"

        lines = [
            "Layer 0 (Identity):     ~%d tokens   [always loaded]" % l0_tokens,
            "Layer 1 (Patterns):     ~%d tokens  [%d active patterns]" % (l1_tokens, active_count),
            "Layer 2 (Session):      ~%d tokens  [current focus]" % l2_tokens,
            "Layer 3 (Deep Search):  on-demand    [ChromaDB: %s]" % chromadb_status,
            "-" * 37,
            "Wake-up total:          ~%d tokens  (was: ~%d tokens with full load)" % (wake_total, full_load),
            "Savings:                ~%d%%" % savings_pct,
        ]

        return "\n".join(lines)

    def _estimate_full_load(self):
        """Estimate token cost of loading full knowledge.md + activeContext.md (old approach)."""
        total = 0
        for rel_path in [
            os.path.join(".claude", "memory", "knowledge.md"),
            os.path.join(".claude", "memory", "activeContext.md"),
        ]:
            fpath = os.path.join(self.project_root, rel_path)
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        total += _token_estimate(f.read())
                except Exception:
                    pass
        return total


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _find_project_root():
    """
    Find the project root by walking up from CWD looking for CLAUDE.md.
    Falls back to CWD if not found.
    """
    cwd = os.getcwd()
    current = cwd
    for _ in range(10):  # max 10 levels up
        if os.path.exists(os.path.join(current, "CLAUDE.md")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    # Also check if script is inside the project
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # .claude/scripts/ -> go up 2 levels
    project_candidate = os.path.dirname(os.path.dirname(script_dir))
    if os.path.exists(os.path.join(project_candidate, "CLAUDE.md")):
        return project_candidate

    logger.warning("_find_project_root: CLAUDE.md not found, using CWD=%s", cwd)
    return cwd


def usage():
    """Print usage and exit."""
    print("context-layers.py -- 4-Layer Context Loading (adapted from MemPalace)")
    print()
    print("Usage:")
    print("  py -3 context-layers.py wake-up          L0+L1+L2 combined (startup injection)")
    print("  py -3 context-layers.py l0               Identity only")
    print("  py -3 context-layers.py l1               Active patterns only")
    print("  py -3 context-layers.py l2               Session context only")
    print("  py -3 context-layers.py l3 \"query here\"  Deep search")
    print("  py -3 context-layers.py stats            Token counts per layer")
    print()
    print("Options:")
    print("  --root=/path/to/project   Override project root auto-detection")
    print("  DEBUG=1                   Enable debug logging to stderr")
    sys.exit(0)


def main():
    """CLI entry point."""
    # Fix Windows encoding (cp1251/cp1252 can't handle unicode dashes/arrows from memory files)
    if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        usage()

    cmd = sys.argv[1]
    logger.debug("main: cmd=%s, args=%s", cmd, sys.argv[2:])

    # Parse flags
    flags = {}
    positional = []
    for arg in sys.argv[2:]:
        if arg.startswith("--") and "=" in arg:
            key, val = arg.split("=", 1)
            flags[key.lstrip("-")] = val
        elif not arg.startswith("--"):
            positional.append(arg)

    project_root = flags.get("root", _find_project_root())
    logger.info("main: project_root=%s", project_root)

    stack = ContextStack(project_root)

    if cmd in ("wake-up", "wakeup"):
        print(stack.wake_up())

    elif cmd == "l0":
        print("## L0 -- PROJECT IDENTITY")
        print(stack.l0.render())

    elif cmd == "l1":
        print(stack.l1.generate())

    elif cmd == "l2":
        print(stack.l2.render())

    elif cmd == "l3":
        query = " ".join(positional) if positional else ""
        if not query:
            print("Usage: py -3 context-layers.py l3 \"query here\"")
            sys.exit(1)
        print(stack.search(query))

    elif cmd == "stats":
        print(stack.stats())

    else:
        print("Unknown command: %s" % cmd, file=sys.stderr)
        usage()


if __name__ == "__main__":
    main()
