import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("knowledge-decay-report.py")
SPEC = importlib.util.spec_from_file_location("knowledge_decay_report", SCRIPT_PATH)
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)


def write_memory(root, knowledge_text, active_text=None):
    memory = Path(root) / ".claude" / "memory"
    memory.mkdir(parents=True)
    knowledge_path = memory / "knowledge.md"
    knowledge_path.write_text(knowledge_text, encoding="utf-8")
    if active_text is not None:
        (memory / "activeContext.md").write_text(active_text, encoding="utf-8")
    return knowledge_path


class KnowledgeDecayReportTests(unittest.TestCase):
    def make_report(self, text, today="2026-04-25", active_text=None, include_gotchas=True):
        with tempfile.TemporaryDirectory() as root:
            knowledge_path = write_memory(root, text, active_text)
            return report.make_report(
                knowledge_path,
                date.fromisoformat(today),
                include_gotchas,
                (14, 30, 90),
            )

    def test_fresh_entry_active(self):
        data = self.make_report("## Patterns\n### Fresh (2026-04-20, verified: 2026-04-20)\n")
        self.assertEqual(data["tiers"]["active"][0]["tier"], "active")

    def test_twenty_days_warm(self):
        data = self.make_report("## Patterns\n### Warm One (2026-04-05, verified: 2026-04-05)\n")
        self.assertEqual(data["summary"]["warm"], 1)

    def test_sixty_days_cold(self):
        data = self.make_report("## Patterns\n### Cold One (2026-02-24, verified: 2026-02-24)\n")
        self.assertEqual(data["tiers"]["cold"][0]["age_days"], 60)

    def test_hundred_twenty_days_archive(self):
        data = self.make_report("## Patterns\n### Old One (2025-12-26, verified: 2025-12-26)\n")
        self.assertEqual(data["summary"]["archive"], 1)

    def test_missing_verified_unparsed(self):
        data = self.make_report("## Patterns\n### Missing Verified (2026-01-01)\n")
        self.assertEqual(data["tiers"]["unparsed"][0]["tier"], "unparsed")

    def test_today_override_applied(self):
        data = self.make_report("## Patterns\n### Override (2026-04-01, verified: 2026-04-01)\n", today="2026-04-08")
        self.assertEqual(data["tiers"]["active"][0]["age_days"], 7)

    def test_patterns_only_excludes_gotchas(self):
        text = "## Patterns\n### Pattern A (2026-04-20, verified: 2026-04-20)\n## Gotchas\n### Gotcha A (2026-04-20, verified: 2026-04-20)\n"
        data = self.make_report(text, include_gotchas=False)
        self.assertEqual(data["summary"]["total"], 1)
        self.assertEqual(data["tiers"]["active"][0]["name"], "Pattern A")

    def test_json_schema_round_trip(self):
        data = self.make_report("## Patterns\n### Json One (2026-04-20, verified: 2026-04-20)\n")
        loaded = json.loads(json.dumps(data))
        self.assertEqual(set(["generated_at", "today", "tiers", "summary"]).issubset(loaded), True)
        self.assertEqual(set(loaded["tiers"]["active"][0]), set(["name", "verified", "created", "age_days", "tier", "line_no"]))

    def test_promotion_candidate_detection(self):
        text = "## Patterns\n### Promote Me (2026-04-01, verified: 2026-04-01)\n"
        data = self.make_report(text, active_text="We should revisit promote me today.")
        self.assertEqual(data["promotion_candidates"][0]["name"], "Promote Me")

    def test_empty_knowledge_total_zero(self):
        data = self.make_report("")
        self.assertEqual(data["summary"]["total"], 0)


if __name__ == "__main__":
    unittest.main()
