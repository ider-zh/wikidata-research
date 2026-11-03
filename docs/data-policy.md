# Storage, privacy, source licenses, and caching

## Immutable boundaries

| Class | Allowed location | Not allowed |
| --- | --- | --- |
| Full Wikidata dump | local disk / private object storage | GitHub, Hugging Face |
| Wikipedia HTML/wikitext responses | 30-day local cache / private source store | GitHub, Hugging Face |
| Agent traces and incomplete records | local/private processing store | public release |
| Small synthetic fixtures, prompts, schemas, tests | GitHub | embedded real dumps/article bodies |
| Verified and human-accepted structured records | Hugging Face Dataset | publication without evidence/approval |
| Reports, charts, provenance manifests | GitHub and dataset card | unlicensed verbatim reproductions |

This policy is enforced initially by Git ignore rules and required release checks. A future publisher must implement an explicit allowlist for accepted files and refuse input under `raw/`, `cache/`, `data/` staging, or source dump paths.

## 30-day Wikipedia cache

- Fetch using the article language/title obtained from Wikidata sitelinks.
- Cache key: language + title; store response, page ID, revision ID, original source URL, and retrieval timestamp.
- A hit less than 30 days old returns local content. On expiry fetch again and atomically replace the cache entry. There is no global cache eviction job yet.
- A cache is a source retrieval optimization, not permission to ignore a source revision. Individual extracted claims cite their actual source revisions.
- The cache is not committed, packaged into the public website, or uploaded to Hugging Face.

## Licensing

Wikidata structured statements are provided under CC0. Wikipedia text and its translations or adaptations require appropriate attribution and licensing review (typically CC BY-SA). Historical gazetteers have source-specific licenses. Do **not** blanket-license mixed provenance data as CC0 merely because Wikidata was one of the sources.

Data releases should include a source/license registry and cite the precise page revision, source language, and author/project attribution where required. Choose code and dataset licenses explicitly before the first public release.
