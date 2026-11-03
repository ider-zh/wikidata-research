import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from wikidata_research.wikipedia import WikipediaCache


class WikipediaCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = datetime(2026, 11, 3, tzinfo=timezone.utc)
        self.urls = []

    def fake_fetch(self, url):
        self.urls.append(url)
        if url.endswith("/html"):
            return b"<html><body>University page</body></html>"
        return json.dumps({"id": 123, "title": "University of Oxford", "latest": {"id": 987}}).encode()

    def cache(self):
        return WikipediaCache(
            self.temp.name, ttl_days=30, fetch_bytes=self.fake_fetch, now=lambda: self.now
        )

    def test_hit_within_30_days_and_refresh_after_expiry(self):
        cache = self.cache()
        first = cache.get_page("en", "University of Oxford")
        self.assertFalse(first.from_cache)
        self.assertEqual(first.revision_id, 987)
        self.assertEqual(len(self.urls), 2)
        self.now += timedelta(days=29)
        self.assertTrue(cache.get_page("en", "University of Oxford").from_cache)
        self.assertEqual(len(self.urls), 2)
        self.now += timedelta(days=1, seconds=1)
        self.assertFalse(cache.get_page("en", "University of Oxford").from_cache)
        self.assertEqual(len(self.urls), 4)

    def test_language_validation(self):
        with self.assertRaises(ValueError):
            self.cache().get_page("evil.example/path", "Oxford")
        self.assertEqual(len(self.urls), 0)

    def test_separate_languages_and_encoded_titles(self):
        self.cache().get_page("fr", "Université d'Oxford")
        self.assertEqual(len(self.urls), 2)
        self.assertIn("fr.wikipedia.org", self.urls[0])
        self.assertIn("Universit%C3%A9_d%27Oxford", self.urls[0])


if __name__ == "__main__":
    unittest.main()
