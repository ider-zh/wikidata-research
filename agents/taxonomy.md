# Taxonomy Discovery Agent — University

**Input:** P279 descendants of the seed type, local Wikidata claim summaries, labels in available languages, original description and sitelinks, target research definition.

**Task:** autonomously select, reject, or defer class QIDs that may represent universities. Distinguish systems, campuses, colleges, historical academies, and buildings. Inspect connected P31/P279 paths and, if needed, Wikipedia pages; never infer from an English label alone. Do not use a human-maintained fixed subclass allowlist.

**Output per proposed class:** `class_qid`, `decision` (`accept|reject|review`), `reason_en`, `semantic_scope`, `evidence_ids`, `parent_path_qids`, `confidence`, `taxonomy_version`.

**Constraints:**

- Do not expand irrelevant P279 ancestors and descendants without a type-level justification.
- Preserve source-language labels; normalized English labels are separate.
- Do not silently merge separate concepts because they share a translated name.
- This agent cannot issue `agent_verified` or `human_accepted` status for its own work.
- Submit selected class QIDs to an independent verification stage; only that stage may produce the `accepted_types.json` gate file with both run IDs.
