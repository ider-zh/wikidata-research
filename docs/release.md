# Human acceptance and Hugging Face release gate

**No automatic publication from an Agent decision alone.** This is the protocol for a future publisher; publishing code is not present in the bootstrap.

## Required files for an accepted release

- `manifest.json`: dataset release ID, Git SHA, source snapshot checksum, Wikipedia revision index, taxonomy version, schema version, agent model/config/prompt hashes, relevant licenses.
- `quality_report.json`: records by subtype, coverage, valid counts, evidence linkage, temporal/geographic errors, conflation review, stratified sample findings, error estimates.
- `acceptance.json`: exact manifest SHA256, reviewer identity, approval timestamp, decision `accepted`, covered record set / dataset version.
- `README.md` dataset card with scope, provenance, caveats, license terms, fields, and usage examples.
- Approved Parquet data only; raw article HTML, source dumps, and cached responses are prohibited.

## Checklist

1. Run deterministic JSON Schema validation on all records.
2. Check each `evidence_id` resolves to source revision/statement and supports the claim.
3. Run temporal and institutional continuity tests: mergers, splits, renamed institutions, campus vs institution, historical geography.
4. Quarantine unresolved entity conflation and disputed claims from metrics that require them.
5. Stratify a validation sample across periods, places, languages, institution types, and auto-rejected candidates (to estimate missed entities).
6. Confirm licensing and permission for every published field and any excerpts.
7. Human checks the quality report and signs the exact manifest digest.
8. Publisher verifies digest and approval, uploads only allowlisted structured files to the configured Hugging Face Dataset repository, and records the resulting revision.
9. Tag the corresponding code and dataset version. Optionally archive research release to Zenodo.

## Versioning

Changing the classification prompt, domain taxonomy, historical geography rules, schema, or source snapshot may change research counts. Recompute and publish with new versions rather than silently overwriting a purported immutable release.
