# Wikidata Research

An agent-assisted, evidence-first research workbench for extracting multilingual, structured knowledge from local Wikidata dumps and online Wikipedia articles.

**First study:** universities (`studies/university`). The same workflow is intended to support people, libraries, research institutes, and other well-defined entity types.

## Principles

1. **Local Wikidata only.** Candidate discovery reads a user-supplied Wikidata JSON dump on local storage. It never downloads a dump automatically or commits raw Wikidata data.
2. **Online Wikipedia with a 30-day disk cache.** Fetch pages by Wikidata sitelink; preserve page ID, revision ID, language, and source URL. Cache files and raw page content stay local.
3. **Agent-driven taxonomy.** Agents propose and review P279 subclass expansions, P31 instance types, and domain-relevant predicates. No fixed manually curated P279/P101 allowlist is the authoritative classifier.
4. **Evidence before inference.** Every accepted structured claim links to a specific source revision and excerpt. Unknowns, contradictions, historical ambiguity, and potential entity conflation are explicit states.
5. **Human final acceptance.** Agents perform classification, extraction, identity reconciliation, and verification. Humans approve dataset releases and evaluate samples; agents cannot self-authorize publication.
6. **Publish only processed, approved datasets.** The public dataset destination is Hugging Face. GitHub and Hugging Face must never receive raw Wikidata dumps, cached Wikipedia pages, or unreviewed large intermediate extracts.

## Current status

This repository contains a **tested bootstrap**, not a completed extraction campaign. It includes a streaming dump reader, subclass-type discovery, an initial university candidate exporter, an online Wikipedia client with a 30-day cache, schemas, agent contracts, and release-policy scaffolding. The LLM execution provider, complete event extraction, historical geocoding, and Hugging Face publication are follow-on implementations. No dataset has been published.

## Local setup

Python 3.11+; the bootstrap runtime uses only the Python standard library.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

### 1. Discover university subclasses from a local dump

```bash
wikidata-research discover-types \
  --dump /path/to/latest-all.json.bz2 \
  --seed Q3918 \
  --output data/university/taxonomy_candidates.json
```

This produces **taxonomy candidates**, not accepted taxonomy decisions. The taxonomy agent must assess the candidate subclasses against the University study policy before the accepted type list is used.

### 2. Export an initial high-recall university candidate list

```bash
wikidata-research candidates \
  --dump /path/to/latest-all.json.bz2 \
  --types data/university/accepted_types.json \
  --output data/university/candidates.jsonl
```

If `--types` is omitted, only the root university type `Q3918` is used for a safe bootstrap, and descendants may be missed. The generated list is **pending agent review**.

### 3. Retrieve a Wikipedia page via the 30-day local cache

```bash
wikidata-research fetch-page \
  --language en \
  --title 'University of Oxford' \
  --cache-dir cache/wikipedia
```

The command reports provenance metadata, not the raw article. The HTML is stored under the ignored local cache directory. Page selection for the production pipeline comes from Wikidata sitelinks; do not guess titles by translating entity names.

## Project layout

| Path | Purpose |
| --- | --- |
| `src/wikidata_research/` | Local dump processing and cached online page access |
| `agents/` | Agent instructions and structured output contracts |
| `schemas/` | Versioned JSON Schemas |
| `studies/university/` | University-specific research definition and edge cases |
| `workflows/` | Machine-readable pipeline stage contract |
| `docs/` | Architecture, provenance, licensing, acceptance, and publication policies |
| `tests/` | Offline, deterministic tests |

## Storage and releases

- **GitHub:** source code, prompts, configuration, schemas, small fixtures, quality policies, and reports.
- **Local/private object storage:** Wikidata dumps, Wikipedia cache, agent traces, and unfinished datasets.
- **Hugging Face Dataset repository:** only human-accepted structured outputs with a dataset card, evidence provenance, quality report, and a release manifest.
- **Zenodo (optional):** archived, citation-ready snapshots after an accepted release.

See [architecture](docs/architecture.md), [data policy](docs/data-policy.md), [release checklist](docs/release.md), and the [University study specification](studies/university/README.md).

## 中文说明

项目目标是构建可扩展的 Wikidata/Wikipedia 多语言知识研究工作流。第一阶段处理大学实体；后续可扩展到科学人物、图书馆和研究机构。Agent 自动完成 P279 分类探索、身份审核、事实抽取与核验，人工只负责最终验收。原始 Wikidata dump 与 Wikipedia 页面缓存不上传 GitHub 或 Hugging Face，只有验收通过的结构化数据才可发布。
