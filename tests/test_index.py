import bz2
import json
from pathlib import Path
import tempfile
import unittest

from wikidata_research.candidates import read_agent_accepted_types, wikipedia_sitelinks
from wikidata_research.index import build_index, index_taxonomy, index_candidates
from test_dumps import sample_entities, statement


class LocalIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dump = self.root / "synthetic.json.bz2"
        entities = sample_entities()
        entities[1]["claims"]["P279"][0].update(id="Q100$synthetic", references=[{"hash": "test"}])
        # Cycle must not duplicate proposals or prevent traversal from reaching the seed.
        entities[1]["claims"]["P279"].append(statement("Q101"))
        entities[4]["claims"]["P31"][0]["id"] = "Q200$synthetic"
        self.dump.write_bytes(bz2.compress(("[\n" + ",\n".join(map(json.dumps, entities))
                                            + "\n]\n").encode()))
        self.index = self.root / "local.sqlite"

    def records(self, name):
        return [json.loads(line) for line in (self.root / name).read_text().splitlines()]

    def test_one_scan_then_evidence_and_candidates_without_dump(self):
        report = build_index(self.dump, self.index)
        self.assertEqual(report["item_entities_read"], 6)
        self.assertTrue(report["scan_complete"])
        self.assertFalse(report["publication_allowed"])
        self.dump.unlink()  # Subsequent operations must not read the source again.
        result = index_taxonomy(self.index, self.root / "types.jsonl", {"Q3918"})
        self.assertEqual(result["candidate_type_count"], 3)
        types = {r["qid"]: r for r in self.records("types.jsonl")}
        self.assertEqual(types["Q101"]["parent_path_qids"], ["Q101", "Q100", "Q3918"])
        self.assertNotIn("Q102", types)
        claim = types["Q100"]["p279_statements"][1]
        self.assertEqual(claim["id"], "Q100$synthetic")
        self.assertEqual(claim["references"], [{"hash": "test"}])
        result = index_candidates(self.index, self.root / "candidates.jsonl", {"Q3918", "Q101"})
        self.assertEqual(result["candidate_entity_count"], 1)
        record = self.records("candidates.jsonl")[0]
        self.assertEqual(record["qid"], "Q200")
        self.assertEqual(record["p31_statements"][0]["id"], "Q200$synthetic")
        self.assertEqual(record["wikipedia_sitelinks"], {"en": "Test University"})
        # Revising type selection needs no dump rescan.
        self.assertEqual(index_candidates(self.index, self.root / "other.jsonl", {"Q3918"})
                         ["candidate_entity_count"], 0)

    def test_partial_scan_marking_is_propagated(self):
        build_index(self.dump, self.index, max_entities=2)
        self.assertFalse(index_taxonomy(self.index, self.root / "types.jsonl", {"Q3918"})
                         ["scan_complete"])
        self.assertTrue(all(not r["scan_complete"] for r in self.records("types.jsonl")))
        self.assertFalse(index_candidates(self.index, self.root / "candidates.jsonl", {"Q101"})
                         ["scan_complete"])

    def test_failed_rebuild_keeps_previous_index(self):
        build_index(self.dump, self.index)
        original = self.index.read_bytes()
        self.dump.write_bytes(bz2.compress(b"[\n{broken json\n"))
        with self.assertRaises(ValueError):
            build_index(self.dump, self.index)
        self.assertEqual(self.index.read_bytes(), original)
        self.assertEqual(list(self.root.glob("*.building.sqlite*")), [])

    def test_source_and_index_cannot_be_output(self):
        with self.assertRaises(ValueError):
            build_index(self.dump, self.dump)
        build_index(self.dump, self.index)
        with self.assertRaises(ValueError):
            index_taxonomy(self.index, self.index, {"Q3918"})
        with self.assertRaises(ValueError):
            index_candidates(self.index, self.index, {"Q3918"})

    def test_accepted_types_need_distinct_runs_and_valid_qids(self):
        path = self.root / "accepted.json"
        base = {"status": "agent_verified", "taxonomy_agent_run_id": "classify",
                "verification_agent_run_id": "verify", "accepted_type_qids": ["Q3918"]}
        for update in ({"verification_agent_run_id": "classify"},
                       {"accepted_type_qids": ["Qnot-an-id"]}, {"scan_complete": False}):
            path.write_text(json.dumps(base | update))
            with self.subTest(update=update), self.assertRaises(ValueError):
                read_agent_accepted_types(path)

    def test_only_wikipedia_sitelinks(self):
        self.assertEqual(wikipedia_sitelinks({"sitelinks": {
            "enwiki": {"title": "University"}, "commonswiki": {"title": "Category:Universities"},
            "specieswiki": {"title": "Species"}, "enwikivoyage": {"title": "Travel"},
            "zh_classicalwiki": {"title": "大學"},
        }}), {"en": "University", "zh-classical": "大學"})
