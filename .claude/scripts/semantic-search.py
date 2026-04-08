#!/usr/bin/env python3
"""
Semantic search across Claude Code memory layers using ChromaDB embeddings.

Adapted from MemPalace searcher.py + miner.py (github.com/milla-jovovich/mempalace) -- MIT License

Indexes .claude/memory/ files (knowledge.md, daily/*.md, observations/*.md, activeContext.md)
and JSONL session transcripts into ChromaDB for meaning-based retrieval.

Usage:
    py -3 .claude/scripts/semantic-search.py index                     # reindex all sources
    py -3 .claude/scripts/semantic-search.py index --source knowledge   # index one source
    py -3 .claude/scripts/semantic-search.py search "query" --limit 5   # semantic search
    py -3 .claude/scripts/semantic-search.py status                     # show index stats
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("semantic-search")

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
MIN_CHUNK_SIZE = 50

PALACE_PATH = os.path.expanduser("~/.claude/memory/search_index")
COLLECTION_NAME = "claude_memory"
VALID_SOURCES = {"knowledge", "daily", "observations", "context", "sessions"}


def _require_chromadb():
    """Import chromadb or exit with install instructions."""
    try:
        import chromadb
        logger.debug("chromadb imported, version=%s", chromadb.__version__)
        return chromadb
    except ImportError:
        print("ChromaDB not installed. Run: pip install chromadb>=0.5.0,<0.7")
        sys.exit(1)


def _chunk_by_header(text, header_re):
    """Split markdown text on header regex, return list of {content, header}."""
    logger.debug("Chunking text (%d chars) by pattern: %s", len(text), header_re)
    parts = re.split("(%s)" % header_re, text, flags=re.MULTILINE)
    chunks = []
    current_header = ""
    current_body = ""
    for part in parts:
        if re.match(header_re, part):
            if current_body.strip() and len(current_body.strip()) > MIN_CHUNK_SIZE:
                for sub in _split_long_chunk(current_body.strip(), current_header):
                    chunks.append(sub)
            current_header = part.strip().lstrip("#").strip()
            current_body = part
        else:
            current_body += part
    if current_body.strip() and len(current_body.strip()) > MIN_CHUNK_SIZE:
        for sub in _split_long_chunk(current_body.strip(), current_header):
            chunks.append(sub)
    logger.debug("Produced %d chunks", len(chunks))
    return chunks


def _split_long_chunk(text, header=""):
    """Split text exceeding CHUNK_SIZE with overlap (MemPalace strategy)."""
    if len(text) <= CHUNK_SIZE:
        return [{"content": text, "header": header}]
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk_text = text[start:end]
        if len(chunk_text.strip()) >= MIN_CHUNK_SIZE:
            suffix = " (part %d)" % (len(chunks) + 1) if start > 0 else ""
            chunks.append({"content": chunk_text, "header": header + suffix})
        start = end - CHUNK_OVERLAP
    return chunks


def _chunk_file_as_whole(text, header=""):
    """Treat entire file as one chunk (split if too long)."""
    logger.debug("Chunking whole file (%d chars)", len(text))
    return _split_long_chunk(text.strip(), header) if len(text.strip()) > MIN_CHUNK_SIZE else []


def _chunk_jsonl_sessions(jsonl_path):
    """Chunk JSONL session files by exchange pairs (adapted from convo_miner.py)."""
    logger.debug("Chunking JSONL session: %s", jsonl_path.name)
    chunks = []
    current_user_msg = None
    current_assistant_parts = []
    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
            for line_str in f:
                line_str = line_str.strip()
                if not line_str:
                    continue
                try:
                    entry = json.loads(line_str)
                except json.JSONDecodeError:
                    continue
                entry_type = entry.get("type", "")
                if entry_type == "user":
                    if current_user_msg:
                        _flush_exchange(chunks, current_user_msg, current_assistant_parts, jsonl_path)
                    msg = entry.get("message", {})
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        content = " ".join(p.get("text", "") for p in content if isinstance(p, dict))
                    current_user_msg = str(content).strip()
                    current_assistant_parts = []
                elif entry_type == "assistant":
                    msg = entry.get("message", {})
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        text_parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
                        content = " ".join(text_parts)
                    text = str(content).strip()
                    if text:
                        current_assistant_parts.append(text[:600])
        if current_user_msg:
            _flush_exchange(chunks, current_user_msg, current_assistant_parts, jsonl_path)
    except Exception as e:
        logger.warning("Failed to parse session %s: %s", jsonl_path.name, e)
    logger.debug("Produced %d chunks from session %s", len(chunks), jsonl_path.name)
    return chunks


def _flush_exchange(chunks, user_msg, assistant_parts, jsonl_path):
    """Create a chunk from one user+assistant exchange pair."""
    ai_text = " ".join(assistant_parts[:3])
    combined = "> %s\n%s" % (user_msg, ai_text) if ai_text else "> %s" % user_msg
    if len(combined.strip()) < MIN_CHUNK_SIZE:
        return
    for sub in _split_long_chunk(combined.strip(), "session:%s" % jsonl_path.stem[:8]):
        chunks.append(sub)


def _find_project_root():
    """Walk up from script location to find project root."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    logger.debug("Project root: %s", project_root)
    return project_root


def _find_sessions_dir():
    """Find the Claude Code sessions directory for this project."""
    home = Path(os.path.expanduser("~"))
    projects_dir = home / ".claude" / "projects"
    if not projects_dir.exists():
        return Path("__nonexistent__")
    project_root = _find_project_root()
    project_name = str(project_root).replace("\\", "-").replace("/", "-").replace(":", "-").lstrip("-")
    for candidate in projects_dir.iterdir():
        if candidate.is_dir() and project_name.lower()[:30] in candidate.name.lower():
            logger.debug("Found sessions dir: %s", candidate)
            return candidate
    proj_short = project_root.name.lower()
    for candidate in projects_dir.iterdir():
        if candidate.is_dir() and proj_short in candidate.name.lower():
            return candidate
    return Path("__nonexistent__")


def _collect_chunks(source_filter=None):
    """Collect all chunks from all sources."""
    logger.info("Collecting chunks, source_filter=%s", source_filter)
    project_root = _find_project_root()
    memory_dir = project_root / ".claude" / "memory"
    all_chunks = []
    sources_to_index = VALID_SOURCES if source_filter is None else {source_filter}

    if "knowledge" in sources_to_index:
        kp = memory_dir / "knowledge.md"
        if kp.exists():
            logger.info("Indexing knowledge.md")
            text = kp.read_text(encoding="utf-8", errors="replace")
            for c in _chunk_by_header(text, r"^### .+$"):
                all_chunks.append(dict(c, source="knowledge", file=str(kp)))
            logger.info("knowledge.md: %d chunks", sum(1 for x in all_chunks if x["source"] == "knowledge"))

    if "daily" in sources_to_index:
        dd = memory_dir / "daily"
        if dd.exists():
            logger.info("Indexing daily/")
            cnt = 0
            for md in sorted(dd.glob("*.md")):
                text = md.read_text(encoding="utf-8", errors="replace")
                for c in _chunk_by_header(text, r"^## .+$"):
                    all_chunks.append(dict(c, source="daily", file=str(md)))
                    cnt += 1
            logger.info("daily/: %d chunks", cnt)

    if "observations" in sources_to_index:
        od = memory_dir / "observations"
        if od.exists():
            logger.info("Indexing observations/")
            cnt = 0
            for md in sorted(od.glob("*.md")):
                text = md.read_text(encoding="utf-8", errors="replace")
                for c in _chunk_file_as_whole(text, header=md.stem):
                    all_chunks.append(dict(c, source="observations", file=str(md)))
                    cnt += 1
            logger.info("observations/: %d chunks", cnt)

    if "context" in sources_to_index:
        cp = memory_dir / "activeContext.md"
        if cp.exists():
            logger.info("Indexing activeContext.md")
            text = cp.read_text(encoding="utf-8", errors="replace")
            for c in _chunk_by_header(text, r"^## .+$"):
                all_chunks.append(dict(c, source="context", file=str(cp)))
            logger.info("context: %d chunks", sum(1 for x in all_chunks if x["source"] == "context"))

    if "sessions" in sources_to_index:
        sd = _find_sessions_dir()
        if sd.exists():
            logger.info("Indexing sessions from %s", sd)
            jfiles = sorted(sd.glob("*.jsonl"))
            cnt = 0
            for jf in jfiles:
                for c in _chunk_jsonl_sessions(jf):
                    all_chunks.append(dict(c, source="sessions", file=str(jf)))
                    cnt += 1
            logger.info("sessions/: %d chunks from %d files", cnt, len(jfiles))

    logger.info("Total chunks collected: %d", len(all_chunks))
    return all_chunks


def cmd_index(args):
    """Index memory sources into ChromaDB."""
    chromadb = _require_chromadb()
    source_filter = getattr(args, "source", None)
    if source_filter and source_filter not in VALID_SOURCES:
        logger.error("Invalid source: %s", source_filter)
        sys.exit(1)

    chunks = _collect_chunks(source_filter)
    if not chunks:
        logger.warning("No chunks found")
        print("No content found to index.")
        return

    logger.info("Opening ChromaDB at %s", PALACE_PATH)
    os.makedirs(PALACE_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=PALACE_PATH)

    if source_filter is None:
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.info("Deleted existing collection for full reindex")
        except Exception:
            pass
        col = client.get_or_create_collection(COLLECTION_NAME)
    else:
        col = client.get_or_create_collection(COLLECTION_NAME)
        try:
            existing = col.get(where={"source": source_filter})
            if existing and existing["ids"]:
                col.delete(ids=existing["ids"])
                logger.info("Deleted %d chunks for source=%s", len(existing["ids"]), source_filter)
        except Exception as e:
            logger.debug("Delete failed: %s", e)

    ids, documents, metadatas = [], [], []
    for chunk in chunks:
        cid = hashlib.md5(("%s:%s:%s" % (chunk["source"], chunk["file"], chunk["content"][:200])).encode()).hexdigest()
        ids.append(cid)
        documents.append(chunk["content"])
        metadatas.append({
            "source": chunk["source"],
            "file": Path(chunk["file"]).name,
            "file_path": chunk["file"],
            "header": chunk.get("header", ""),
            "indexed_at": datetime.now().isoformat(),
        })

    batch_size = 5000
    for i in range(0, len(ids), batch_size):
        be = min(i + batch_size, len(ids))
        col.upsert(ids=ids[i:be], documents=documents[i:be], metadatas=metadatas[i:be])
        logger.info("Upserted batch %d-%d of %d", i, be, len(ids))

    logger.info("Indexing complete: %d chunks", len(ids))
    print("Indexed %d chunks into %s" % (len(ids), COLLECTION_NAME))
    print("  Storage: %s" % PALACE_PATH)
    from collections import Counter
    for src, cnt in sorted(Counter(m["source"] for m in metadatas).items()):
        print("  %s: %d chunks" % (src, cnt))


def cmd_search(args):
    """Semantic search across indexed memory."""
    chromadb = _require_chromadb()
    query = args.query
    n_results = args.limit
    source_filter = getattr(args, "source", None)
    logger.info("Searching '%s', limit=%d, source=%s", query, n_results, source_filter)

    try:
        client = chromadb.PersistentClient(path=PALACE_PATH)
        col = client.get_collection(COLLECTION_NAME)
    except Exception:
        print("No index found at %s" % PALACE_PATH)
        print("Run: py -3 .claude/scripts/semantic-search.py index")
        sys.exit(1)

    kwargs = {"query_texts": [query], "n_results": n_results, "include": ["documents", "metadatas", "distances"]}
    if source_filter:
        kwargs["where"] = {"source": source_filter}

    try:
        results = col.query(**kwargs)
    except Exception as e:
        logger.error("Search error: %s", e)
        print("Search error: %s" % e)
        sys.exit(1)

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    if not docs:
        print('No results found for: "%s"' % query)
        return

    print("\n" + "=" * 60)
    print('  Results for: "%s"' % query)
    if source_filter:
        print("  Source filter: %s" % source_filter)
    print("=" * 60 + "\n")

    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists), 1):
        similarity = round(1 - dist, 3)
        source = meta.get("source", "?")
        filename = meta.get("file", "?")
        header = meta.get("header", "")
        print("  [%d] %s / %s" % (i, source, filename))
        if header:
            print("      Section: %s" % header)
        print("      Match:   %s" % similarity)
        print()
        lines = doc.strip().split("\n")
        for line in lines[:20]:
            print("      %s" % line)
        if len(lines) > 20:
            print("      ... (%d more lines)" % (len(lines) - 20))
        print()
        print("  " + "~" * 56)
    print()
    logger.info("Returned %d results", len(docs))


def cmd_status(args):
    """Show index statistics."""
    chromadb = _require_chromadb()
    logger.info("Checking index at %s", PALACE_PATH)

    if not os.path.exists(PALACE_PATH):
        print("No index found at %s" % PALACE_PATH)
        print("Run: py -3 .claude/scripts/semantic-search.py index")
        return

    try:
        client = chromadb.PersistentClient(path=PALACE_PATH)
        col = client.get_collection(COLLECTION_NAME)
    except Exception:
        print("No collection found")
        return

    count = col.count()
    print("\nSemantic Search Index Status")
    print("=" * 40)
    print("  Storage:    %s" % PALACE_PATH)
    print("  Collection: %s" % COLLECTION_NAME)
    print("  Total chunks: %d" % count)

    if count > 0:
        for source in sorted(VALID_SOURCES):
            try:
                result = col.get(where={"source": source})
                sc = len(result["ids"]) if result and result["ids"] else 0
                if sc > 0:
                    print("    %s: %d" % (source, sc))
            except Exception:
                pass
        try:
            sample = col.peek(limit=1)
            if sample and sample["metadatas"]:
                print("  Last indexed: %s" % sample["metadatas"][0].get("indexed_at", "unknown"))
        except Exception:
            pass
    print()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Semantic search across Claude Code memory layers", prog="semantic-search")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    idx = subparsers.add_parser("index", help="Index memory sources into ChromaDB")
    idx.add_argument("--source", choices=sorted(VALID_SOURCES), help="Index only this source")

    sp = subparsers.add_parser("search", help="Semantic search")
    sp.add_argument("query", help="Search query")
    sp.add_argument("--limit", type=int, default=5, help="Max results (default: 5)")
    sp.add_argument("--source", choices=sorted(VALID_SOURCES), help="Filter by source")

    subparsers.add_parser("status", help="Show index statistics")

    args = parser.parse_args()
    if args.command == "index":
        cmd_index(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
