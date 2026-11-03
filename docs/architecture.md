# Architecture and extension model

## Two products, one reproducible pipeline

1. **Reusable research workbench:** agents, connectors, identity resolution, schema discovery, verification, provenance, and release gate.
2. **Study-specific processed datasets:** first universities, later people, libraries, research institutes, and other Wikidata entity types.

Each study provides a target schema, seed concepts, research questions, event taxonomy, quality acceptance criteria, and reporting views. The common pipeline contains no permanent university-only taxonomy whitelist.

## Dataflow

```text
Local Wikidata JSON dump
  -> stream P279 class graph / candidate entity metadata
  -> taxonomy agent -> independent taxonomy verifier
  -> entity candidates (P31, sitelinks, source statements)
  -> identity resolution agent
  -> select multilingual Wikipedia sitelinks
  -> online MediaWiki REST fetch with 30-day LOCAL cache
  -> multilingual extraction agent (original language -> structured English)
  -> source/evidence matching and independent verification agent
  -> schema, temporal, geographic, identity, and provenance validation
  -> versioned approved records + quality report
  -> human final acceptance
  -> processed-only Hugging Face dataset release
```

## Implementation boundaries

- `src/wikidata_research/dumps.py`: local-only streaming Wikidata dump reader.
- `src/wikidata_research/candidates.py`: raw P279 subclass proposal discovery and P31 candidate export; not an LLM classifier.
- `src/wikidata_research/wikipedia.py`: online page retrieval with 30-day cache and revision provenance.
- `agents/*.md`: model-agnostic Agent contracts. A future provider adapter will implement tool-using ReAct and structured outputs.
- `schemas/*.json`: versioned research records.
- `workflows/*.json`: stage machine contract and explicit implementation status.

**Current scope:** only the deterministic adapters above are implemented. The other stages are specified, not simulated. Do not market the bootstrap as a fully automated university extraction system.

## Extension to persons, universities, and libraries

Keep a common `Entity + Claim + Evidence + Time + Place + Event` vocabulary; implement distinct study schemas and Agents:

- Person: birth, death, education, occupation, scholarly activity, migration (not inferred from endpoints).
- University: founding, legal/academic status, campus, mergers, splits, relocation, institution continuity.
- Library: founding, collection provenance, building vs institution, relocation, institutional affiliation, collection transfers.

Entity resolution and historical geocoding can be reused without forcing a person-specific or modern-state-only model on other domains.

## Reproducibility

Every release manifest must identify: source dump snapshot and checksum, Wikipedia page revision IDs and languages, Git SHA, prompts and provider/model configuration, taxonomy agent decisions and verifier run IDs, schema version, quality report, human approver reference, and license/source registry.

Immutable raw source snapshots should be kept locally or in access-controlled object storage. Public repositories contain only approved structured output and necessary provenance, not the originals.
