# Agent operating instructions — wikidata-research

These are repository-level rules for coding agents and research/extraction agents.

## Non-negotiable data boundaries

- Wikidata source: a **local JSON dump** supplied by the operator. Never replace it with a remote SPARQL sweep or an online dump fetch without explicit authorization.
- Wikipedia source: online MediaWiki API, with a **30-day local disk cache**. Cache content by language, title, and retrieval metadata; preserve revision IDs.
- Never commit or publish raw Wikidata dumps, Wikipedia HTML/wikitext caches, bulk source text, unreviewed agent outputs, model credentials, or private logs to GitHub or Hugging Face.
- Approved structured data belongs in a **Hugging Face Dataset repository**; no publication before a human acceptance record exists.
- Keep implementation code and its unit tests in GitHub. Use immutable version identifiers and a manifest for every released dataset.

## Division of responsibility

- **Agents autonomously:** discover candidate P279 classes and P101/P106 domain relations as appropriate; classify entities; detect identity conflation; choose relevant Wikipedia language editions; extract facts from original-language articles; normalize public field names and summaries to English; verify every claim; report uncertainty and conflicts.
- **Deterministic code:** read dumps, manage cache, validate schemas and invariants, track lineage, perform batch processing, retry safely, and enforce the publication gate.
- **Human:** define research goal and acceptance criteria, inspect quality reports and stratified samples, and approve final taxonomy/dataset versions. Do not silently introduce per-entity manual classifications as production ground truth.

## Evidence requirements

- Preserve original labels and excerpts alongside normalized English values. Never translate away a historical name or overwrite a source fact.
- Every source-derived claim must carry `source_language`, `page_id`, `revision_id`, `section` or text locator, source URL, and evidence ID. Wikidata statements must retain statement identifiers and references when available.
- A Wikipedia page, its Wikidata item, and sites copying either do **not** count as three independent sources.
- Unknown is `null` or an explicit uncertainty state. Do not infer death at last residence, a discovery at publication place, or migrations from birth/death endpoints.
- Maintain separate historical and modern geographic attributions with valid times and provenance. Never equate a modern territory with historical nationality.
- Treat suspicious identity merges as `conflation_suspected` and quarantine affected migration or institution-history claims until resolved.

## First domain: University

- Use `studies/university/README.md` for scope and cases, and `schemas/university_record.schema.json` as the record contract.
- Distinguish university institutions, university systems, campuses, colleges, predecessor institutions, faculty units, and buildings.
- Treat name change, relocation, merger, split, legal succession, closure, and change of jurisdiction as distinct events.
- P279 subclasses are **proposals** until an agent decision is recorded and verified; `Q3918` is a bootstrap seed, not a permanent manual whitelist.

## Coding and release workflow

- Keep Python 3.11+ compatibility and tests runnable offline.
- Design provider-specific LLM integration behind an interface. Do not claim agent stages are operational until a provider is configured and verified.
- Record prompt, model/configuration, code commit, input snapshot, taxonomy, schema, and quality-policy versions.
- Never write publishing code that can bypass `accepted` status or a human approval reference.
- Keep public demos compact; don't bundle original Wikimedia dumps or bulk article text in a frontend.
