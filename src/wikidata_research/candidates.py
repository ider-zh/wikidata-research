"""University class discovery and deterministic candidate export.

P279 is *discovered* from the dump. Agent taxonomy review is a separate,
mandatory workflow stage; discovery does not constitute acceptance.
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from .dumps import iter_entities, item_values, labels


ROOT_UNIVERSITY_QID = "Q3918"


def discover_subclass_qids(
    dump_path: str | Path,
    seeds: set[str],
    *,
    max_entities: int | None = None,
    progress_every: int | None = None,
) -> set[str]:
    """Find P279 descendants (including seeds) through reverse graph traversal."""
    children: dict[str, set[str]] = defaultdict(set)
    for entity in iter_entities(dump_path, max_entities=max_entities, progress_every=progress_every):
        child = entity["id"]
        for parent in item_values(entity, "P279"):
            children[parent].add(child)

    discovered = set(seeds)
    queue = deque(seeds)
    while queue:
        for child in children.get(queue.popleft(), ()):
            if child not in discovered:
                discovered.add(child)
                queue.append(child)
    return discovered


def write_taxonomy_proposals(
    dump_path: str | Path,
    output_path: str | Path,
    seeds: set[str],
    *,
    max_entities: int | None = None,
    progress_every: int | None = None,
) -> int:
    proposed = discover_subclass_qids(
        dump_path, seeds, max_entities=max_entities, progress_every=progress_every
    )
    payload = {
        "entity_type": "university",
        "seed_type_qids": sorted(seeds),
        "candidate_type_qids": sorted(proposed),
        "status": "pending_agent_review",
        "scan_complete": max_entities is None,
        "max_entities": max_entities,
        "source_dump_name": Path(dump_path).name,
        "note": "Agent taxonomy and independent verification required before accepted_types export.",
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(proposed)


def read_agent_accepted_types(path: str | Path) -> set[str]:
    """Only consume a taxonomy selection with a recorded agent-verification gate."""
    data: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("status") != "agent_verified":
        raise ValueError("Accepted types require status=agent_verified")
    if not data.get("taxonomy_agent_run_id") or not data.get("verification_agent_run_id"):
        raise ValueError("Accepted types require both agent run identifiers")
    values = data.get("accepted_type_qids")
    if not isinstance(values, list) or not values or any(
        not isinstance(x, str) or not x.startswith("Q") for x in values
    ):
        raise ValueError("accepted_type_qids must be a nonempty list of QIDs")
    return set(values)


def write_university_candidates(
    dump_path: str | Path,
    output_path: str | Path,
    accepted_types: set[str],
    *,
    max_entities: int | None = None,
    progress_every: int | None = None,
) -> int:
    """Write matching entity metadata as NDJSON; never include full dump claims."""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with target.open("w", encoding="utf-8") as stream:
        for entity in iter_entities(
            dump_path, max_entities=max_entities, progress_every=progress_every
        ):
            type_matches = sorted(set(item_values(entity, "P31")) & accepted_types)
            if not type_matches:
                continue
            sitelinks = {
                language[:-4]: item["title"]
                for language, item in entity.get("sitelinks", {}).items()
                if language.endswith("wiki") and isinstance(item.get("title"), str)
            }
            record = {
                "qid": entity["id"],
                "labels": labels(entity),
                "matched_type_qids": type_matches,
                "wikipedia_sitelinks": sitelinks,
                "candidate_status": "pending_agent_review",
                "scan_complete": max_entities is None,
                "source_dump_name": Path(dump_path).name,
            }
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count
