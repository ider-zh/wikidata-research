"""Command-line bootstrap for local Wikidata and cached Wikipedia processing."""

from __future__ import annotations

import argparse
import json

from .candidates import (
    ROOT_UNIVERSITY_QID,
    read_agent_accepted_types,
    write_taxonomy_proposals,
    write_university_candidates,
)
from .wikipedia import WikipediaCache


def main() -> None:
    parser = argparse.ArgumentParser(description="Wikidata Research bootstrap CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    taxonomy = sub.add_parser("discover-types", help="Discover P279 subclasses as agent proposals")
    taxonomy.add_argument("--dump", required=True)
    taxonomy.add_argument("--seed", action="append", default=[])
    taxonomy.add_argument("--output", required=True)

    candidate = sub.add_parser("candidates", help="Stream university candidate records from local dump")
    candidate.add_argument("--dump", required=True)
    candidate.add_argument("--types", help="Agent-verified taxonomy selection JSON")
    candidate.add_argument("--output", required=True)

    wiki = sub.add_parser("fetch-page", help="Fetch a Wikipedia article into 30-day local cache")
    wiki.add_argument("--language", required=True)
    wiki.add_argument("--title", required=True)
    wiki.add_argument("--cache-dir", default="cache/wikipedia")

    args = parser.parse_args()
    if args.command == "discover-types":
        count = write_taxonomy_proposals(args.dump, args.output, set(args.seed or [ROOT_UNIVERSITY_QID]))
        print(json.dumps({"candidate_subclass_count": count, "status": "pending_agent_review"}))
    elif args.command == "candidates":
        accepted = read_agent_accepted_types(args.types) if args.types else {ROOT_UNIVERSITY_QID}
        count = write_university_candidates(args.dump, args.output, accepted)
        print(json.dumps({"candidate_entity_count": count, "status": "pending_agent_review"}))
    elif args.command == "fetch-page":
        page = WikipediaCache(args.cache_dir).get_page(args.language, args.title)
        print(json.dumps({
            "language": page.language, "title": page.title, "page_id": page.page_id,
            "revision_id": page.revision_id, "source_url": page.source_url,
            "retrieved_at": page.retrieved_at, "from_cache": page.from_cache,
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
