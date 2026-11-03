"""Online Wikipedia retrieval with a strictly local 30-day cache."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import quote
from urllib.request import Request, urlopen


DEFAULT_TTL_DAYS = 30
USER_AGENT = "WikidataResearch/0.1 (https://github.com/ider-zh/wikidata-research)"


def _download(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, text/html"})
    with urlopen(request, timeout=30) as response:
        return response.read()


@dataclass(frozen=True)
class WikipediaPage:
    language: str
    title: str
    page_id: int | None
    revision_id: int | None
    source_url: str
    retrieved_at: str
    html: str
    from_cache: bool


class WikipediaCache:
    def __init__(
        self,
        cache_dir: str | Path,
        ttl_days: int = DEFAULT_TTL_DAYS,
        fetch_bytes: Callable[[str], bytes] = _download,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if ttl_days <= 0:
            raise ValueError("ttl_days must be positive")
        self.cache_dir = Path(cache_dir)
        self.ttl = timedelta(days=ttl_days)
        self.fetch_bytes = fetch_bytes
        self.now = now

    def _cache_path(self, language: str, title: str) -> Path:
        key = hashlib.sha256(f"{language}\0{title}".encode("utf-8")).hexdigest()
        return self.cache_dir / language / f"{key}.json"

    def get_page(self, language: str, title: str) -> WikipediaPage:
        language = language.lower()
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,19}", language):
            raise ValueError("Invalid Wikipedia language code")
        if not title.strip():
            raise ValueError("Wikipedia title is required")

        path = self._cache_path(language, title)
        if path.is_file():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                fetched_at = datetime.fromisoformat(payload["retrieved_at"])
                if fetched_at.tzinfo is not None and self.now() - fetched_at < self.ttl:
                    return WikipediaPage(**payload, from_cache=True)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                pass  # damaged cache -> refetch from source

        encoded_title = quote(title.replace(" ", "_"), safe="")
        rest_root = f"https://{language}.wikipedia.org/w/rest.php/v1/page/{encoded_title}"
        info = json.loads(self.fetch_bytes(rest_root).decode("utf-8"))
        html = self.fetch_bytes(rest_root + "/html").decode("utf-8")
        page = WikipediaPage(
            language=language,
            title=info.get("title", title),
            page_id=info.get("id"),
            revision_id=info.get("latest", {}).get("id"),
            source_url=f"https://{language}.wikipedia.org/wiki/{encoded_title}",
            retrieved_at=self.now().isoformat(),
            html=html,
            from_cache=False,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        content = {name: getattr(page, name) for name in (
            "language", "title", "page_id", "revision_id", "source_url", "retrieved_at", "html"
        )}
        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent, delete=False
            ) as tmp:
                temp_path = tmp.name
                json.dump(content, tmp, ensure_ascii=False)
            os.replace(temp_path, path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
        return page
