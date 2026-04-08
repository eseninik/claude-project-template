"""
knowledge-graph.py -- Temporal Entity-Relationship Knowledge Graph
=================================================================

Adapted from MemPalace (github.com/milla-jovovich/mempalace) -- MIT License

Real knowledge graph with:
  - Entity nodes (people, projects, tools, concepts)
  - Typed relationship edges (uses, depends_on, works_on, etc.)
  - Temporal validity (valid_from -> valid_to -- knows WHEN facts are true)
  - Source references (links back to source files/closets)

Storage: SQLite (local, no dependencies, no subscriptions)
Query: entity-first traversal with time filtering

CLI Usage:
    py -3 .claude/scripts/knowledge-graph.py add-entity "Bot Name" --type project
    py -3 .claude/scripts/knowledge-graph.py add-triple "Bot" "uses" "AmoCRM API" --valid-from 2026-01
    py -3 .claude/scripts/knowledge-graph.py query "Bot"
    py -3 .claude/scripts/knowledge-graph.py invalidate "Bot" "uses" "old_auth" --ended 2026-03
    py -3 .claude/scripts/knowledge-graph.py timeline
    py -3 .claude/scripts/knowledge-graph.py stats
    py -3 .claude/scripts/knowledge-graph.py export
"""

import argparse
import hashlib
import json
import logging
import os
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path


# Structured Logging
logger = logging.getLogger("knowledge_graph")


DEFAULT_KG_PATH = os.path.expanduser("~/.claude/memory/knowledge_graph.sqlite3")


class KnowledgeGraph:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_KG_PATH
        logger.info("KnowledgeGraph init: db_path=%s", self.db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        logger.debug("Initializing database schema")
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT DEFAULT 'unknown',
                properties TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS triples (
                id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                valid_from TEXT,
                valid_to TEXT,
                confidence REAL DEFAULT 1.0,
                source_closet TEXT,
                source_file TEXT,
                extracted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject) REFERENCES entities(id),
                FOREIGN KEY (object) REFERENCES entities(id)
            );

            CREATE INDEX IF NOT EXISTS idx_triples_subject ON triples(subject);
            CREATE INDEX IF NOT EXISTS idx_triples_object ON triples(object);
            CREATE INDEX IF NOT EXISTS idx_triples_predicate ON triples(predicate);
            CREATE INDEX IF NOT EXISTS idx_triples_valid ON triples(valid_from, valid_to);
        """)
        conn.commit()
        conn.close()
        logger.debug("Database schema initialized")

    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _entity_id(self, name: str) -> str:
        return name.lower().replace(" ", "_").replace("'", "")

    # ── Write operations ──────────────────────────────────────────────────

    def add_entity(self, name: str, entity_type: str = "unknown", properties: dict = None):
        """Add or update an entity node."""
        eid = self._entity_id(name)
        props = json.dumps(properties or {})
        logger.info("add_entity: name=%s, type=%s, id=%s", name, entity_type, eid)
        conn = self._conn()
        conn.execute(
            "INSERT OR REPLACE INTO entities (id, name, type, properties) VALUES (?, ?, ?, ?)",
            (eid, name, entity_type, props),
        )
        conn.commit()
        conn.close()
        logger.debug("add_entity complete: id=%s", eid)
        return eid

    def add_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        valid_from: str = None,
        valid_to: str = None,
        confidence: float = 1.0,
        source_closet: str = None,
        source_file: str = None,
    ):
        """
        Add a relationship triple: subject → predicate → object.

        Examples:
            add_triple("Max", "child_of", "Alice", valid_from="2015-04-01")
            add_triple("Max", "does", "swimming", valid_from="2025-01-01")
            add_triple("Alice", "worried_about", "Max injury", valid_from="2026-01", valid_to="2026-02")
        """
        sub_id = self._entity_id(subject)
        obj_id = self._entity_id(obj)
        pred = predicate.lower().replace(" ", "_")
        logger.info("add_triple: %s -[%s]-> %s (from=%s, to=%s)", subject, pred, obj, valid_from, valid_to)

        # Auto-create entities if they don't exist
        conn = self._conn()
        conn.execute("INSERT OR IGNORE INTO entities (id, name) VALUES (?, ?)", (sub_id, subject))
        conn.execute("INSERT OR IGNORE INTO entities (id, name) VALUES (?, ?)", (obj_id, obj))

        # Check for existing identical triple
        existing = conn.execute(
            "SELECT id FROM triples WHERE subject=? AND predicate=? AND object=? AND valid_to IS NULL",
            (sub_id, pred, obj_id),
        ).fetchone()

        if existing:
            logger.debug("add_triple: already exists id=%s, skipping", existing[0])
            conn.close()
            return existing[0]  # Already exists and still valid

        triple_id = f"t_{sub_id}_{pred}_{obj_id}_{hashlib.md5(f'{valid_from}{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}"

        conn.execute(
            """INSERT INTO triples (id, subject, predicate, object, valid_from, valid_to, confidence, source_closet, source_file)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                triple_id,
                sub_id,
                pred,
                obj_id,
                valid_from,
                valid_to,
                confidence,
                source_closet,
                source_file,
            ),
        )
        conn.commit()
        conn.close()
        logger.info("add_triple complete: id=%s", triple_id)
        return triple_id

    def invalidate(self, subject: str, predicate: str, obj: str, ended: str = None):
        """Mark a relationship as no longer valid (set valid_to date)."""
        sub_id = self._entity_id(subject)
        obj_id = self._entity_id(obj)
        pred = predicate.lower().replace(" ", "_")
        ended = ended or date.today().isoformat()
        logger.info("invalidate: %s -[%s]-> %s, ended=%s", subject, pred, obj, ended)

        conn = self._conn()
        cursor = conn.execute(
            "UPDATE triples SET valid_to=? WHERE subject=? AND predicate=? AND object=? AND valid_to IS NULL",
            (ended, sub_id, pred, obj_id),
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        logger.info("invalidate complete: %d rows updated", affected)
        return affected

    # ── Query operations ──────────────────────────────────────────────────

    def query_entity(self, name: str, as_of: str = None, direction: str = "outgoing"):
        """
        Get all relationships for an entity.

        direction: "outgoing" (entity → ?), "incoming" (? → entity), "both"
        as_of: date string — only return facts valid at that time
        """
        eid = self._entity_id(name)
        logger.info("query_entity: name=%s, as_of=%s, direction=%s", name, as_of, direction)
        conn = self._conn()

        results = []

        if direction in ("outgoing", "both"):
            query = "SELECT t.*, e.name as obj_name FROM triples t JOIN entities e ON t.object = e.id WHERE t.subject = ?"
            params = [eid]
            if as_of:
                query += " AND (t.valid_from IS NULL OR t.valid_from <= ?) AND (t.valid_to IS NULL OR t.valid_to >= ?)"
                params.extend([as_of, as_of])
            for row in conn.execute(query, params).fetchall():
                results.append(
                    {
                        "direction": "outgoing",
                        "subject": name,
                        "predicate": row[2],
                        "object": row[10],  # obj_name
                        "valid_from": row[4],
                        "valid_to": row[5],
                        "confidence": row[6],
                        "source_closet": row[7],
                        "current": row[5] is None,
                    }
                )

        if direction in ("incoming", "both"):
            query = "SELECT t.*, e.name as sub_name FROM triples t JOIN entities e ON t.subject = e.id WHERE t.object = ?"
            params = [eid]
            if as_of:
                query += " AND (t.valid_from IS NULL OR t.valid_from <= ?) AND (t.valid_to IS NULL OR t.valid_to >= ?)"
                params.extend([as_of, as_of])
            for row in conn.execute(query, params).fetchall():
                results.append(
                    {
                        "direction": "incoming",
                        "subject": row[10],  # sub_name
                        "predicate": row[2],
                        "object": name,
                        "valid_from": row[4],
                        "valid_to": row[5],
                        "confidence": row[6],
                        "source_closet": row[7],
                        "current": row[5] is None,
                    }
                )

        conn.close()
        logger.info("query_entity complete: %d results", len(results))
        return results

    def query_relationship(self, predicate: str, as_of: str = None):
        """Get all triples with a given relationship type."""
        pred = predicate.lower().replace(" ", "_")
        logger.info("query_relationship: predicate=%s, as_of=%s", pred, as_of)
        conn = self._conn()
        query = """
            SELECT t.*, s.name as sub_name, o.name as obj_name
            FROM triples t
            JOIN entities s ON t.subject = s.id
            JOIN entities o ON t.object = o.id
            WHERE t.predicate = ?
        """
        params = [pred]
        if as_of:
            query += " AND (t.valid_from IS NULL OR t.valid_from <= ?) AND (t.valid_to IS NULL OR t.valid_to >= ?)"
            params.extend([as_of, as_of])

        results = []
        for row in conn.execute(query, params).fetchall():
            results.append(
                {
                    "subject": row[10],
                    "predicate": pred,
                    "object": row[11],
                    "valid_from": row[4],
                    "valid_to": row[5],
                    "current": row[5] is None,
                }
            )
        conn.close()
        logger.info("query_relationship complete: %d results", len(results))
        return results

    def timeline(self, entity_name: str = None):
        """Get all facts in chronological order, optionally filtered by entity."""
        logger.info("timeline: entity=%s", entity_name)
        conn = self._conn()
        if entity_name:
            eid = self._entity_id(entity_name)
            rows = conn.execute(
                """
                SELECT t.*, s.name as sub_name, o.name as obj_name
                FROM triples t
                JOIN entities s ON t.subject = s.id
                JOIN entities o ON t.object = o.id
                WHERE (t.subject = ? OR t.object = ?)
                ORDER BY t.valid_from ASC NULLS LAST
                LIMIT 100
            """,
                (eid, eid),
            ).fetchall()
        else:
            rows = conn.execute("""
                SELECT t.*, s.name as sub_name, o.name as obj_name
                FROM triples t
                JOIN entities s ON t.subject = s.id
                JOIN entities o ON t.object = o.id
                ORDER BY t.valid_from ASC NULLS LAST
                LIMIT 100
            """).fetchall()

        conn.close()
        return [
            {
                "subject": r[10],
                "predicate": r[2],
                "object": r[11],
                "valid_from": r[4],
                "valid_to": r[5],
                "current": r[5] is None,
            }
            for r in rows
        ]

    # ── Stats ─────────────────────────────────────────────────────────────

    def stats(self):
        """Get summary statistics about the knowledge graph."""
        logger.info("stats: computing")
        conn = self._conn()
        entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        triples = conn.execute("SELECT COUNT(*) FROM triples").fetchone()[0]
        current = conn.execute("SELECT COUNT(*) FROM triples WHERE valid_to IS NULL").fetchone()[0]
        expired = triples - current
        predicates = [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT predicate FROM triples ORDER BY predicate"
            ).fetchall()
        ]
        entity_types = [r[0] for r in conn.execute("SELECT DISTINCT type FROM entities ORDER BY type").fetchall()]
        conn.close()
        logger.info("stats complete: entities=%d, triples=%d, current=%d", entities, triples, current)
        return {
            "entities": entities,
            "triples": triples,
            "current_facts": current,
            "expired_facts": expired,
            "relationship_types": predicates,
            "entity_types": entity_types,
        }

    # ── Seed from known facts ─────────────────────────────────────────────

    def seed_from_entity_facts(self, entity_facts: dict):
        """Seed the knowledge graph from a dictionary of entity facts."""
        logger.info("seed_from_entity_facts: %d entities", len(entity_facts))
        for key, facts in entity_facts.items():
            name = facts.get("full_name", key.capitalize())
            etype = facts.get("type", "unknown")
            self.add_entity(name, etype, {k: v for k, v in facts.items() if k not in ("full_name", "type", "relationships")})
            for rel in facts.get("relationships", []):
                self.add_triple(name, rel.get("predicate", "related_to"), rel.get("object", ""),
                    valid_from=rel.get("valid_from"), valid_to=rel.get("valid_to"))
        logger.info("seed_from_entity_facts complete")


    # -- Export ---------------------------------------------------------------

    def export_markdown(self):
        """Export all current facts as markdown for injection into prompts."""
        logger.info("export_markdown: generating")
        conn = self._conn()

        lines = ["# Knowledge Graph Export", ""]
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        lines.append("")

        entity_types = conn.execute("SELECT DISTINCT type FROM entities ORDER BY type").fetchall()
        for (etype,) in entity_types:
            entities = conn.execute(
                "SELECT name, properties FROM entities WHERE type = ? ORDER BY name", (etype,)
            ).fetchall()
            if entities:
                lines.append(f"## Entities: {etype}")
                for name, props_json in entities:
                    props = json.loads(props_json) if props_json and props_json != "{}" else None
                    if props:
                        lines.append(f"- **{name}** ({json.dumps(props)})")
                    else:
                        lines.append(f"- **{name}**")
                lines.append("")

        rows = conn.execute("""
            SELECT s.name, t.predicate, o.name, t.valid_from, t.confidence
            FROM triples t JOIN entities s ON t.subject = s.id JOIN entities o ON t.object = o.id
            WHERE t.valid_to IS NULL ORDER BY s.name, t.predicate
        """).fetchall()

        if rows:
            lines.append("## Current Facts")
            current_subject = None
            for sub_name, pred, obj_name, valid_from, confidence in rows:
                if sub_name != current_subject:
                    current_subject = sub_name
                    lines.append(f"\n### {sub_name}")
                since = f" (since {valid_from})" if valid_from else ""
                conf = f" [confidence: {confidence}]" if confidence and confidence < 1.0 else ""
                lines.append(f"- {pred} -> **{obj_name}**{since}{conf}")
            lines.append("")

        expired_rows = conn.execute("""
            SELECT s.name, t.predicate, o.name, t.valid_from, t.valid_to
            FROM triples t JOIN entities s ON t.subject = s.id JOIN entities o ON t.object = o.id
            WHERE t.valid_to IS NOT NULL ORDER BY t.valid_to DESC LIMIT 50
        """).fetchall()

        if expired_rows:
            lines.append("## Expired Facts (most recent)")
            for sub_name, pred, obj_name, valid_from, valid_to in expired_rows:
                period = f"{valid_from or '?'} -> {valid_to}"
                lines.append(f"- ~~{sub_name} {pred} {obj_name}~~ ({period})")
            lines.append("")

        conn.close()
        result = "\n".join(lines)
        logger.info("export_markdown complete: %d lines", len(lines))
        return result


# -- CLI Interface ------------------------------------------------------------


def _format_results(results: list, title: str = "Results") -> str:
    """Format query results for CLI output."""
    if not results:
        return f"{title}: (none)"
    lines = [f"{title} ({len(results)}):", ""]
    for r in results:
        current_mark = "[CURRENT]" if r.get("current") else "[EXPIRED]"
        period = ""
        if r.get("valid_from") or r.get("valid_to"):
            vf = r.get("valid_from", "?")
            vt = r.get("valid_to", "now")
            period = f" ({vf} -> {vt})"
        direction = f" [{r['direction']}]" if "direction" in r else ""
        sub = r.get("subject", "?")
        pred = r.get("predicate", "?")
        obj = r.get("object", "?")
        lines.append(f"  {current_mark} {sub} -[{pred}]-> {obj}{period}{direction}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Temporal Knowledge Graph -- entity-relationship store with time validity",
        prog="knowledge-graph",
    )
    parser.add_argument("--db", default=None, help=f"Database path (default: {DEFAULT_KG_PATH})")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_ae = subparsers.add_parser("add-entity", help="Add or update an entity")
    p_ae.add_argument("name", help="Entity name")
    p_ae.add_argument("--type", default="unknown", help="Entity type")
    p_ae.add_argument("--properties", default=None, help="JSON properties string")

    p_at = subparsers.add_parser("add-triple", help="Add a relationship triple")
    p_at.add_argument("subject", help="Subject entity")
    p_at.add_argument("predicate", help="Relationship type")
    p_at.add_argument("object", help="Object entity")
    p_at.add_argument("--valid-from", default=None, help="Start date")
    p_at.add_argument("--valid-to", default=None, help="End date")
    p_at.add_argument("--confidence", type=float, default=1.0, help="Confidence 0.0-1.0")
    p_at.add_argument("--source", default=None, help="Source file reference")

    p_q = subparsers.add_parser("query", help="Query entity relationships")
    p_q.add_argument("name", help="Entity name to query")
    p_q.add_argument("--as-of", default=None, help="Filter to facts valid at this date")
    p_q.add_argument("--direction", default="both", choices=["outgoing", "incoming", "both"])

    p_qr = subparsers.add_parser("query-rel", help="Query by relationship type")
    p_qr.add_argument("predicate", help="Relationship type")
    p_qr.add_argument("--as-of", default=None, help="Date filter")

    p_inv = subparsers.add_parser("invalidate", help="Mark a relationship as ended")
    p_inv.add_argument("subject", help="Subject entity")
    p_inv.add_argument("predicate", help="Relationship type")
    p_inv.add_argument("object", help="Object entity")
    p_inv.add_argument("--ended", default=None, help="End date (default: today)")

    p_tl = subparsers.add_parser("timeline", help="Show facts chronologically")
    p_tl.add_argument("entity", nargs="?", default=None, help="Optional entity filter")

    subparsers.add_parser("stats", help="Show graph statistics")
    subparsers.add_parser("export", help="Export all current facts as markdown")

    args = parser.parse_args()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    kg = KnowledgeGraph(db_path=args.db)

    if args.command == "add-entity":
        props = json.loads(args.properties) if args.properties else None
        eid = kg.add_entity(args.name, args.type, props)
        print(f"Entity added: {args.name} (id={eid}, type={args.type})")

    elif args.command == "add-triple":
        tid = kg.add_triple(args.subject, args.predicate, args.object,
            valid_from=args.valid_from, valid_to=args.valid_to,
            confidence=args.confidence, source_file=args.source)
        print(f"Triple added: {args.subject} -[{args.predicate}]-> {args.object} (id={tid})")

    elif args.command == "query":
        results = kg.query_entity(args.name, as_of=args.as_of, direction=args.direction)
        print(_format_results(results, f"Entity: {args.name}"))

    elif args.command == "query-rel":
        results = kg.query_relationship(args.predicate, as_of=args.as_of)
        print(_format_results(results, f"Relationship: {args.predicate}"))

    elif args.command == "invalidate":
        count = kg.invalidate(args.subject, args.predicate, args.object, ended=args.ended)
        ended_str = args.ended or date.today().isoformat()
        print(f"Invalidated: {args.subject} -[{args.predicate}]-> {args.object} ended={ended_str} ({count} rows)")

    elif args.command == "timeline":
        results = kg.timeline(entity_name=args.entity)
        title = f"Timeline: {args.entity}" if args.entity else "Timeline: all"
        print(_format_results(results, title))

    elif args.command == "stats":
        s = kg.stats()
        print("Knowledge Graph Stats:")
        print(f"  Entities:      {s['entities']}")
        print(f"  Triples:       {s['triples']}")
        print(f"  Current facts: {s['current_facts']}")
        print(f"  Expired facts: {s['expired_facts']}")
        ets = ", ".join(s["entity_types"]) or "(none)"
        rts = ", ".join(s["relationship_types"]) or "(none)"
        print(f"  Entity types:  {ets}")
        print(f"  Relationships: {rts}")

    elif args.command == "export":
        md = kg.export_markdown()
        print(md)


if __name__ == "__main__":
    main()
