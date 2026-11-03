import bz2
import gzip
import json
import tempfile
import unittest
from pathlib import Path

from wikidata_research.candidates import (
    discover_subclass_qids,
    read_agent_accepted_types,
    write_university_candidates,
)
from wikidata_research.dumps import iter_entities, item_values


def statement(qid, rank="normal"):
    return {
        "rank": rank,
        "mainsnak": {"datavalue": {"value": {"entity-type": "item", "id": qid}}},
    }


def sample_entities():
    return [
        {"id": "Q3918", "type": "item", "labels": {"en": {"value": "university"}}},
        {"id": "Q100", "type": "item", "claims": {"P279": [statement("Q3918")]}},
        {"id": "Q101", "type": "item", "claims": {"P279": [statement("Q100")]}},
        {"id": "Q102", "type": "item", "claims": {"P279": [statement("Q3918", "deprecated")]}},
        {
            "id": "Q200", "type": "item", "claims": {"P31": [statement("Q101")]},
            "labels": {"en": {"value": "Test University"}},
            "sitelinks": {"enwiki": {"title": "Test University"}},
        },
        {"id": "Q201", "type": "item", "claims": {"P31": [statement("Q102")]}},
        {"id": "P31", "type": "property", "claims": {}},
    ]


class WikidataDumpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "sample.json"
        self.path.write_text(
            "[\n" + ",\n".join(json.dumps(e) for e in sample_entities()) + "\n]\n",
            encoding="utf-8",
        )

    def test_plain_gzip_and_bz2_stream(self):
        data = self.path.read_bytes()
        (self.path.parent / "sample.json.gz").write_bytes(gzip.compress(data))
        (self.path.parent / "sample.json.bz2").write_bytes(bz2.compress(data))
        for suffix in ("", ".gz", ".bz2"):
            with self.subTest(suffix=suffix):
                items = list(iter_entities(str(self.path) + suffix))
                self.assertEqual(len(items), 6)

    def test_subclass_discovery_skips_deprecated(self):
        found = discover_subclass_qids(self.path, {"Q3918"})
        self.assertEqual(found, {"Q3918", "Q100", "Q101"})

    def test_candidates_are_pending_review_and_metadata_only(self):
        destination = self.path.parent / "candidates.ndjson"
        count = write_university_candidates(self.path, destination, {"Q3918", "Q100", "Q101"})
        self.assertEqual(count, 1)
        result = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual(result["qid"], "Q200")
        self.assertEqual(result["wikipedia_sitelinks"], {"en": "Test University"})
        self.assertEqual(result["candidate_status"], "pending_agent_review")
        self.assertNotIn("claims", result)

    def test_requires_independent_agent_verification(self):
        selection = self.path.parent / "accepted.json"
        selection.write_text(json.dumps({"status": "agent_verified", "accepted_type_qids": ["Q100"]}))
        with self.assertRaisesRegex(ValueError, "both agent run identifiers"):
            read_agent_accepted_types(selection)
        selection.write_text(json.dumps({
            "status": "agent_verified",
            "taxonomy_agent_run_id": "agent-1",
            "verification_agent_run_id": "verify-1",
            "accepted_type_qids": ["Q3918", "Q100"],
        }))
        self.assertEqual(read_agent_accepted_types(selection), {"Q3918", "Q100"})

    def test_deprecated_statement_not_used(self):
        self.assertEqual(item_values(sample_entities()[3], "P279"), [])


if __name__ == "__main__":
    unittest.main()
