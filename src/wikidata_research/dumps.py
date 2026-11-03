"""Stream Wikidata JSON-array dumps without loading the dump into memory.

Wikidata's latest-all JSON dump is a JSON array with one entity per line.
Supported inputs are plain .json, .json.gz, and .json.bz2 files. This reader
intentionally does not download or upload source data.
"""

from __future__ import annotations

import bz2
import gzip
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any
import sys


def _open_text(path: Path):
    if path.name.endswith(".bz2"):
        return bz2.open(path, "rt", encoding="utf-8")
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("rt", encoding="utf-8")


def iter_entities(
    path: str | Path,
    *,
    max_entities: int | None = None,
    progress_every: int | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield entities without loading the dump into memory.

    `max_entities` enables a clearly incomplete smoke run, not a dataset count.
    Progress counts emitted to stderr are parsed item entities, not file lines.
    """
    if max_entities is not None and max_entities <= 0:
        raise ValueError("max_entities must be positive")
    if progress_every is not None and progress_every <= 0:
        raise ValueError("progress_every must be positive")
    source = Path(path)
    count = 0
    with _open_text(source) as stream:
        for line_number, raw_line in enumerate(stream, start=1):
            line = raw_line.strip()
            if not line or line in ("[", "]"):
                continue
            if line.endswith(","):
                line = line[:-1]
            try:
                entity = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Malformed Wikidata entity at {source}:{line_number}; "
                    "expected one JSON entity per line"
                ) from exc
            if not isinstance(entity, dict):
                raise ValueError(f"Expected a Wikidata object at {source}:{line_number}")
            if entity.get("type") == "item" and str(entity.get("id", "")).startswith("Q"):
                count += 1
                yield entity
                if progress_every and count % progress_every == 0:
                    print(f"scanned {count:,} Wikidata item entities", file=sys.stderr, flush=True)
                if max_entities is not None and count >= max_entities:
                    return


def item_values(entity: dict[str, Any], property_id: str) -> list[str]:
    """Return item-QIDs from non-deprecated statements of a property."""
    result: list[str] = []
    for claim in entity.get("claims", {}).get(property_id, []):
        if claim.get("rank") == "deprecated":
            continue
        snak = claim.get("mainsnak", {})
        value = snak.get("datavalue", {}).get("value", {})
        if isinstance(value, dict) and isinstance(value.get("id"), str):
            qid = value["id"]
            if qid.startswith("Q"):
                result.append(qid)
    return list(dict.fromkeys(result))


def labels(entity: dict[str, Any], languages: tuple[str, ...] = ("en", "zh", "fr")) -> dict[str, str]:
    source = entity.get("labels", {})
    return {
        lang: source[lang]["value"]
        for lang in languages
        if lang in source and isinstance(source[lang].get("value"), str)
    }
