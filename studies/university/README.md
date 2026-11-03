# University — first research entity type

## Objective

Build a versioned, evidence-backed English-normalized dataset of universities and their histories. Wikidata provides candidate entities from a **local dump**; Wikipedia is fetched **online and cached for 30 days**. Agent classification and extraction decisions remain revisable; publication requires human final acceptance.

## Scope: deliberate distinctions

| Item | Inclusion decision |
| --- | --- |
| A degree-granting university | Candidate: classify by era and jurisdiction |
| A university system with several institutions | Separate organization type; do not merge with campuses |
| A constituent college or faculty | Relationship to university; not automatically the same university |
| A campus / building | Place or facility; not automatically a university entity |
| Historical academy / medieval university | Context-sensitive Agent review; do not impose modern degree criteria retroactively |
| A renamed university | Usually same entity + dated name claim, unless identity evidence indicates legal discontinuity |
| Merged universities | Distinct predecessors and successor; record explicit merger/succession event |
| Defunct institution | Keep it with closure event, not excluded solely for being defunct |

## Wikidata candidate discovery

- Start from the university root type `Q3918` and explore P279 subclass links in the local dump.
- **The taxonomy agent selects and judges** candidate subclasses; an independent verification agent checks the selection. Discovery is not a whitelist and is not a final acceptance decision.
- Use P31, historical names, inception, administrative location, organization structure, and available Wikipedia sitelinks as classification evidence. P101/P106 are domain-specific to other studies such as people and must not be treated as mandatory university properties.
- Do not turn a source's present-day country into a historical-country assertion.

## University-specific event taxonomy

`founded`, `opened`, `renamed`, `relocated`, `merged`, `split`, `closed`, `reopened`, `status_changed`, `affiliation_changed`, `campus_opened`, `campus_closed`.

For each event record a time interval or precision, the university entity, participants/predecessors/successors, place ID or uncertain region, original-language evidence, normalized English description, and explicit relation to the institution.

## Required quality edge cases

1. Institution renamed but did not relocate.
2. University moved between cities, while retaining institutional continuity.
3. One university split into two successor institutions.
4. Two institutions merged, but one legacy name remained in use.
5. Historical university closed and a new institution later adopted the name.
6. University has several campuses in different countries; headquarters is not every campus.
7. Regional historical boundaries changed without physical relocation.
8. Wikipedia language editions conflate different institutions sharing a name.
9. A college acquired university status at a later date.
10. Founding date versus first teaching date versus charter date differs.

## Acceptance criteria for first published dataset

- Schema and evidence checks pass for all released records.
- Every published fact has a traceable, versioned source; missing fields remain `null`.
- Identity conflation cases are quarantined or explicitly resolved.
- Stratified samples cover eras, geography, multilingual sources, and entity subtypes.
- A quality report lists sample counts, precision estimates, coverage, conflicts, and exclusions.
- Human signs off the exact dataset version and manifest hash; only approved structured data is uploaded to Hugging Face.
