"""Fast read-only preflight of a local Wikidata dump.

Probe intentionally reads only the first N item entities. Its counts are NOT
dataset statistics; it cannot establish whole-file integrity or completeness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .dumps import iter_entities


def probe_dump(path: str | Path, max_entities: int = 2000) -> dict[str, Any]:
    if max_entities <= 0:
        raise ValueError("max_entities must be positive")
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Local Wikidata dump not found: {source}")
    if source.suffix == ".bz2":
        compression = "bzip2"
        expected_magic = b"BZh"
    elif source.suffix == ".gz":
        compression = "gzip"
        expected_magic = b"\x1f\x8b"
    else:
        compression = "plain"
        expected_magic = None
    with source.open("rb") as raw:
        if expected_magic and raw.read(len(expected_magic)) != expected_magic:
            raise ValueError(f"File extension and compression header disagree: {source.name}")

    first_qids: list[str] = []
    last_qid: str | None = None
    scanned = 0
    for entity in iter_entities(source, max_entities=max_entities):
        scanned += 1
        if len(first_qids) < 5:
            first_qids.append(entity["id"])
        last_qid = entity["id"]

    return {
        "source_filename": source.name,
        "compressed_size_bytes": source.stat().st_size,
        "compression": compression,
        "item_entities_read": scanned,
        "max_entities": max_entities,
        "first_qids": first_qids,
        "last_qid": last_qid,
        "status": "partial_read_only_preflight",
        "full_dump_validated": False,
        "whole_dump_count_available": False,
        "note": "First-N items are not a representative sample and do not establish dump completeness.",
    }
