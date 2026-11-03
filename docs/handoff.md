# Development handoff — 2026-11-03

## Goal and constraints

Continue `ider-zh/wikidata-research` with **University as the first entity type**. The framework should later support other entities, such as libraries and people. Read `AGENTS.md`, `studies/university/README.md`, and `docs/data-policy.md` before changing behavior.

- Wikidata comes only from an operator-supplied **local dump**. Do not replace it with an API/SPARQL sweep or download a different snapshot automatically.
- The newest dump is still downloading. Predevelopment should use the existing **2026-05-04 JSON BZ2 snapshot**. Obtain the server and absolute path from the operator's conversation or local environment; do not commit private connection details.
- Wikipedia is fetched online and cached locally for **30 days**. Record the precise page revision used as evidence.
- Raw Wikidata, Wikipedia source/cache, unreviewed outputs, local indices and credentials remain local. GitHub holds implementation and rules. Only human-accepted structured research data may be published to Hugging Face.
- Agents discover, select and independently verify the classification; humans perform final acceptance. `Q3918` is a discovery seed, not a permanent manual whitelist.

## Verified environment state

This work ran in a cloud container. An SSH connection to the operator's LAN server returned `Network is unreachable` before authentication. Switching to Work mode did not provide a route to that LAN. **No real dump data has been read, counted, extracted, or published.** Continue in an environment that can reach the server, or run directly on that server. Do not request a password to solve a routing failure.

Repository history entering this session:

- `d3f62fdd39a99ec346863d886cd526f337b0030d`: initial framework and University study.
- `9cdc8d7d512a6ec538949115abccc524b4b38a59`: bounded preflight and dump smoke commands.

The commit containing this handoff adds:

| Component | Implemented behavior |
| --- | --- |
| `build-index` | One local dump pass creates a disk-backed SQLite P31/P279 index; completed builds replace the destination atomically |
| `index-types` | Emits local taxonomy evidence packets: labels, descriptions, sitelinks, P279 statements with references, and a path to the discovery seed |
| `index-candidates` | Uses an independently verified type selection to export candidates and matching P31 source statements without rescanning the dump |
| Classification gate | Rejects identical classifier/verifier run IDs, malformed QIDs, and an explicitly incomplete selection |
| Sitelinks | Excludes Commons, Wikispecies and central Wikimedia projects from Wikipedia language links |
| Offline tests | 18 tests pass, including compressed synthetic input, cycles, deprecated statements, retained provenance, partial marking and failed-build preservation |

All new fixtures are synthetic. Runtime uses the Python 3.11+ standard library. There is **no operational LLM provider adapter, batch Wikipedia runner, full extraction pipeline, or Hugging Face publisher** yet.

## Next-window startup

1. Clone/pull `main`; inspect `git log -3 --oneline` and `git status --short`. If this handoff commit is absent, fetch the repository before starting new work.
2. Confirm the server is reachable, authenticate using the operator's existing SSH setup, and check that the 2026-05-04 dump is readable. Check Python version, CPU/RAM and free space beside the intended local index.
3. Run the following **on the machine holding the dump**, substituting the operator's actual dump path. This is a shell variable, not a committed configuration value:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v

WIKIDATA_SOURCE='/absolute/path/to/wikidata-20260504-all.json.bz2'
test -r "$WIKIDATA_SOURCE"
wikidata-research probe --dump "$WIKIDATA_SOURCE" --max-entities 2000

wikidata-research build-index \
  --dump "$WIKIDATA_SOURCE" \
  --index data/university/smoke.sqlite \
  --max-entities 20000

wikidata-research index-types \
  --index data/university/smoke.sqlite \
  --output data/university/taxonomy-smoke.jsonl
```

These first-N results are not representative samples and cannot establish university counts, taxonomy coverage, or dump integrity. If the prefix contains few university-related classes, do not widen the classifier by inventing an allowlist. Use a verified full scan or a deliberately designed local test sample.

4. Follow `docs/predevelopment.md` section 6 for full indexing after checking the source's download/checksum. Run lengthy jobs in a durable server session and retain local progress logs. Index ingestion currently restarts from the beginning after interruption; do not advertise compressed seek/resume support.

## Development priorities

1. **Fix Wikipedia revision/content consistency before batch evidence extraction.** `wikipedia.py` currently requests REST page metadata and `/html` separately. An edit between requests can pair a revision ID with a different body. Use a revision-bound request or a single response containing body and revision ID; preserve an immutable revision URL and body hash. Refetch legacy cache entries whose pairing cannot be verified. Review the official [MediaWiki parse API](https://www.mediawiki.org/wiki/API:Parsing_wikitext) (`page`/`oldid`, `text`, `revid`) before selecting an implementation. Pinning the article revision does not freeze historical template expansion; retain the fetched content hash locally.
2. **Connect an actual Agent runner behind a provider interface.** No provider, model or credentials have been selected or tested. Record prompt/model/config versions, input hashes and independent run IDs. `agents/taxonomy.md` and `agents/verification.md` define the roles. The new taxonomy packets are the input. Do not fake `agent_verified` or ask the human to manually classify each class.
3. **Add persistent task state and Wikipedia batch retrieval.** Agent-selected languages must come from real sitelinks. Store pending/running/succeeded/failed state, bounded retries, pacing, errors and page provenance; rerun failures without replaying completed work. The current single-page cache is the only implemented retrieval unit.
4. **Tighten lineage and integrity.** Index source fingerprint currently records filename/size/mtime, not SHA256. Record an operator-verified checksum, bind taxonomy decisions to the exact index/snapshot and policy version, and strengthen truncated JSON-array checks. `scan_complete: true` currently means an unbounded iterator reached EOF, not that the source checksum was verified. A seed without any indexed P31/P279 statements has a minimal proposal without labels and needs local source enrichment.
5. **University extraction and quality reports.** Implement identity review, multilingual event extraction, source checks and temporal/geographic validation against the existing schema. Keep unknowns and conflicts explicit; distinguish institutions, systems, campuses, faculties, buildings and predecessor entities.
6. **Final acceptance and publication.** Generate release manifests and quality reports. The human acceptance gate remains mandatory. Implement the Hugging Face publisher only after these records exist; no target dataset repository has been created or selected.

## Suggested continuation instruction

> Continue the University workflow in `ider-zh/wikidata-research`. Read `AGENTS.md` and `docs/handoff.md` first. Use the existing local 2026-05-04 Wikidata dump on the server specified in my conversation. Check connectivity and run probe plus a bounded SQLite-index smoke test. Then implement the listed priorities with real provenance and independently verified Agent stages. Keep all source data local, and report the difference between offline tests and real-source validation.
