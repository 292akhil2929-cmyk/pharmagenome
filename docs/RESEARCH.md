# Drug-target and pathway research methods

Phase 5 connects the existing ten-gene cohort to a pinned Open Targets snapshot. These are gene-level research associations, not patient matching, variant-specific sensitivity or treatment recommendations.

## Source scope
Official Ensembl symbol lookup resolves each existing Entrez/symbol pair to an Ensembl target. Open Targets target responses supply names, Reactome pathways and drug/clinical candidate associations. A drug-target link is accepted only when at least one source mechanism explicitly contains that Ensembl target. Complex membership can map a mechanism to multiple targets; this does not establish selective binding.

Snapshot retrieved 2026-09-08:
- 10 genes, 183 distinct source drug identifiers, 186 drug-target links.
- 220 distinct Reactome pathways, 279 gene-pathway memberships.
- 6,712 distinct source/report-ID pairs across associations.
- 186 downloaded candidate rows = 186 accepted + 0 invalid + 0 excluded + 0 duplicate rows.
- 1,052 unmapped disease-label occurrences are counted and omitted from disease filtering; raw responses retain them.
- SHA-256: a203c4635eac2cdb679f4081c1163a730d70f78745b54f17b566ebf5b5c3b3cb.

| Gene | Source drug links | Pathways |
|---|---:|---:|
| BRAF | 18 | 16 |
| EGFR | 82 | 37 |
| KRAS | 3 | 71 |
| MET | 38 | 19 |
| NF1 | 0 | 2 |
| PIK3CA | 32 | 60 |
| RB1 | 0 | 18 |
| STK11 | 0 | 4 |
| TP53 | 9 | 46 |
| KEAP1 | 4 | 6 |

Scope is limited to returned source associations, not every experimentally measured binding interaction. No binding affinities, dose, response or efficacy measurements are supplied.

## Evidence meaning
Drug type is the source modality label, not a therapeutic class. Maximum clinical stage is Open Targets' harmonized historical label and is not a current, indication-specific approval assessment. Disease labels describe source-associated research; they are not the cohort's disease or automatically approved indications.

Clinical reports are heterogeneous records, including trials, regulatory labels and other references, and may include warnings or withdrawals. Count distinct (source, report ID) pairs after selection. One trial can appear for multiple drugs. Do not sum drug report counts as independent studies or interpret record count as evidence strength.

[Open Targets documents upstream LLM extraction](https://platform-docs.opentargets.org/drug/clinical-report.md) for AACT trial drug/disease entities. PharmaGenome preserves source labels without independently validating those assignments. Its own analysis requires no LLM.

## Computation
1. Select a completed source snapshot and one or more imported genes.
2. Select candidate links for those genes; optionally restrict links by source disease ID.
3. Filter linked drugs by literal name/ID search, modality or source maximum stage.
4. Deduplicate drugs by source identifier and reports by source/ID. Sort deterministically by name/ID, or descending report count with name/ID ties.
5. Independently collect pathway memberships for the selected genes. Rank by distinct selected genes in each pathway, then pathway name and identifier.

The displayed overlap denominator is the full selected gene count, including genes with no membership. It is not full pathway size. Drug filters never alter pathway overlap. No background universe, enrichment test, p-value or arbitrary pathway score is calculated.

Disease filtering selects associations; report lists retain all source records for each selected association. The focused network shows at most three pathways and three drugs from the current pages for one selected gene. Nodes can open details; no drug-pathway causality is inferred.

## Reproducibility and API
GET /api/research supports dataset_id, genes (comma-separated), q, drug_class, disease, stage, sort (name/reports), page, pathway_page and page_size (1–100; default 20). Unknown genes and invalid numeric bounds receive 422. Absent snapshots receive 404; unavailable databases receive 503. Search is literal. The API reads one immutable snapshot through parameterized SQL.

JSON export includes full details for the current drug/pathway pages, complete filtered summary, selected genes, parameters, timestamp, method/version, code revision, source SHA and limitations. It explicitly labels page scope; request further pages to export more records.

## Pipeline
Capture runs in GitHub Actions, never during public requests. It verifies identity, source response counts, nonempty metadata, URL schemes, mechanism mapping, conflicts and duplicate records. Raw/manifest checksums are verified before replay. Invalid records block the database transaction. Legacy HTTP source URLs are preserved, not silently rewritten.

New snapshot metadata and all associations are versioned. Foreign keys preserve scoped membership. An advisory lock makes each import atomic and idempotent. Synthetic data is rejected for production. No destructive migration or live source fetch occurs in public request handlers.

From backend:
```sh
python -m scripts.capture_associations --output capture/new-research-snapshot
python -m scripts.capture_associations --replay --output data/research_associations
python -m scripts.migrate
python -m scripts.load_associations
```

The Vercel backend build and Docker migration service load both pinned snapshots. Raw content remains at backend/data/research_associations. See [source terms](../backend/data/research_associations/SOURCE_LICENSE.md).

## Verification
Backend tests reconcile the pinned public snapshot, validate EGFR's 82 links and 37 pathways through PostgreSQL/API, test older snapshot preservation, idempotency, source truncation, checksum tampering, unsafe links, unmapped mechanisms, conflicting duplicates, distinct report counts, literal search, pagination and pathway denominator independence. Browser tests separately use labeled synthetic fixtures for layout and interaction evidence.
