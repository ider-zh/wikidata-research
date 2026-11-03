# Predevelopment against a local Wikidata snapshot

This runbook is intended to be executed **on the machine that already stores the dump**. The public GitHub repository never receives the dump or the private server's address/path.

## 1. Prepare the environment

```bash
git clone https://github.com/ider-zh/wikidata-research.git
cd wikidata-research
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

Use a local shell variable containing the absolute path to the existing dump:

```bash
WIKIDATA_SOURCE='/absolute/path/to/wikidata-YYYYMMDD-all.json.bz2'
test -r "$WIKIDATA_SOURCE"
```

## 2. Fast preflight (bounded read)

```bash
wikidata-research probe --dump "$WIKIDATA_SOURCE" --max-entities 2000
```

Expected: `partial_read_only_preflight`, a compressed file size, and some item QIDs. This **does not** prove that a potentially still-downloading dump is complete. Verify the source download completion and checksum separately using its provider's manifest before a full production scan.

## 3. Bounded smoke scan

```bash
wikidata-research discover-types \
  --dump "$WIKIDATA_SOURCE" \
  --max-entities 20000 \
  --output data/university/taxonomy-smoke.json

wikidata-research candidates \
  --dump "$WIKIDATA_SOURCE" \
  --max-entities 20000 \
  --output data/university/candidates-smoke.jsonl
```

Both are deliberately incomplete because the first N QIDs are not a representative sample. Do not infer population counts or publish these outputs.

## 4. Full initial pass (after checksum and local resource check)

```bash
wikidata-research discover-types \
  --dump "$WIKIDATA_SOURCE" \
  --output data/university/taxonomy-candidates.json
```

The complete P279 candidates are then sent to the future taxonomy and independent verification Agents. Only their verified `accepted_types.json` output can drive the expanded P31 candidate export:

```bash
wikidata-research candidates \
  --dump "$WIKIDATA_SOURCE" \
  --types data/university/accepted_types.json \
  --output data/university/university-candidates.jsonl
```

These two full operations scan the compressed dump sequentially. Expect lengthy disk/CPU work. Progress is written to stderr every million parsed entities. Do not assume the process failed because it takes substantial time to decompress the snapshot.

## 5. Evidence and source handling

- Candidate output remains under ignored `data/`.
- Wikipedia HTML remains under ignored `cache/` (30-day TTL).
- Never upload the raw dump or cached Wikipedia pages to GitHub, Hugging Face, or CI artifacts.
- The current implementation has no LLM provider adapter, no bulk Wikipedia scraper, no accepted university dataset, and no Hugging Face publisher. Those are explicit follow-on work items.
- To diagnose a run remotely, share only the short `probe` JSON or selected aggregate counters, not raw source records or source HTML.

## 6. Disk-backed index (recommended for large snapshots)

The SQLite index stores P31/P279 statements (including statement IDs, qualifiers and references when present), labels, descriptions, and Wikipedia sitelinks. It is a **local source derivative**, not a releasable dataset. It can be large: check free disk space before full indexing. SQLite uses a 32 MiB page cache; total process memory also includes the current parsed entity and Python/runtime buffers.

Start with a bounded smoke run:

```bash
wikidata-research build-index \
  --dump "$WIKIDATA_SOURCE" \
  --index data/university/smoke.sqlite \
  --max-entities 20000

wikidata-research index-types \
  --index data/university/smoke.sqlite \
  --output data/university/taxonomy-smoke.jsonl
```

After the source download and checksum have been checked, build a separate full index:

```bash
wikidata-research build-index \
  --dump "$WIKIDATA_SOURCE" \
  --index data/university/full.sqlite

wikidata-research index-types \
  --index data/university/full.sqlite \
  --output data/university/taxonomy-proposals.jsonl
```

Each taxonomy proposal contains an actual P279 path to a seed plus direct P279 source statements. These are inputs to classification, **not** automatic acceptance. Once the taxonomy Agent and a separate verification Agent have produced a valid `accepted_types.json`:

```bash
wikidata-research index-candidates \
  --index data/university/full.sqlite \
  --types data/university/accepted_types.json \
  --output data/university/candidates.jsonl
```

Changing the accepted type selection requires no additional dump decompression. Candidate records retain their matching P31 source statements and remain pending identity review.

Index builds replace the destination only after success; failed builds leave an existing index intact. **Index ingestion does not yet resume after interruption**: rerun it from the start. Exports are atomic. A bounded index propagates `scan_complete: false` to every exported record. `scan_complete` describes scan scope, not external checksum verification or research acceptance. The source fingerprint records filename, size and modification time; it is not a cryptographic content identity. Full builds must use an operator-verified stable source.
