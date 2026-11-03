import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_json_configs_and_schema_are_valid_json(self):
        for relative in (
            "studies/university/config.json",
            "workflows/university.json",
            "schemas/university_record.schema.json",
        ):
            with self.subTest(relative=relative):
                json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_first_study_never_publishes_original_sources(self):
        config = json.loads((ROOT / "studies/university/config.json").read_text())
        self.assertEqual(config["wikidata"]["mode"], "local_dump_only")
        self.assertEqual(config["wikipedia"]["cache_ttl_days"], 30)
        self.assertEqual(config["publication"]["destination"], "huggingface_dataset")
        self.assertFalse(config["publication"]["source_dumps_allowed"])
        self.assertFalse(config["publication"]["wikipedia_raw_pages_allowed"])
        self.assertFalse(config["publication"]["unreviewed_outputs_allowed"])


if __name__ == "__main__":
    unittest.main()
