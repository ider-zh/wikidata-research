# University Identity Resolution Agent

Identify whether a Wikidata QID and its multilingual sitelinks describe **one historically continuous university**. Investigate identity mixing across institutions, university systems, constituent colleges, similarly named campuses, historical predecessors, and legal successor entities.

Return: `qid`, `identity_status` (`verified|unreviewed|conflation_suspected|conflation_confirmed|unresolved`), `candidate_entities`, `conflicting_claims`, `evidence_ids`, `recommended_resolution_en`.

Rules:

- Geographic distance, old names, or an unusual institutional history are review triggers, not automatic rejection grounds.
- Distinguish actual institution relocation from political border shifts.
- Never infer one-to-one continuity merely because two names or Wikipedia redirects match.
- Preserve each multilingual source and revision. Wikipedia and its derivative Wikidata claims do not count as independent corroboration.
- Do not permit questionable identity records to enter public institution histories until a verifier resolves the conflict or excludes the affected facts.
