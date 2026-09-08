# Data sources

## Imported: TCGA lung adenocarcinoma
Source: [cBioPortal study](https://www.cbioportal.org/study/summary?id=luad_tcga_pan_can_atlas_2018), Lung Adenocarcinoma (TCGA, PanCancer Atlas). The captured study is public. Mutation profile: `luad_tcga_pan_can_atlas_2018_mutations`; full sequenced sample list: `luad_tcga_pan_can_atlas_2018_sequenced`.

Retrieved 2026-09-08 at 07:40:20 UTC. Snapshot SHA-256: `aae580bb94295d59dfa7e18676fd7ce62547881958bd0919169f0b1bcc1ca78f`.

| Scope | Value |
|---|---|
| Complete profiled cohort | 566 samples |
| Selected genes | BRAF, EGFR, KRAS, MET, NF1, PIK3CA, RB1, STK11, TP53, KEAP1 |
| Raw mutation records | 966 |
| Accepted sample–SNV observations | 839 |
| Unique GRCh37 SNV identities | 506 |
| Excluded non-SNV records | 127 |
| Invalid / duplicate records | 0 / 0 |
| Accepted observations missing tumour VAF | 0 |

The 86.85% acceptance fraction measures scope retention, not scientific accuracy. A sample without an accepted SNV is not a confirmed wild-type sample. Selected gene membership describes this import's coverage; it does not establish per-base assay callability.

## Provenance and use
The [cBioPortal API documentation](https://docs.cbioportal.org/web-api-and-clients/) describes the official endpoints. Original response bytes, per-file URLs, timestamps and checksums are in [backend/data/luad_snv](backend/data/luad_snv). The manifest checksum is the SHA-256 of newline-joined, filename-sorted `filename:file_sha256` entries. It is not the hash of the manifest JSON itself. The original manifest and raw files are immutable; the database also records pipeline version and import Git revision.

Under the [cBioPortal FAQ](https://docs.cbioportal.org/user-guide/faq/), public portal data defaults to the ODC Open Database License; study-specific restrictions can apply. Cite cBioPortal and the original TCGA PanCancer Atlas work (Cell, 2018). See [NCI TCGA data use](https://www.cancer.gov/ccg/research/genome-sequencing/tcga/using-tcga-data). The repository software license does not relicense source datasets.

GRCh37 chromosome bounds are captured from [Ensembl assembly metadata](https://grch37.rest.ensembl.org/info/assembly/homo_sapiens?content-type=application/json). [Endpoint documentation](https://rest.ensembl.org/documentation/info/assembly_info). Bounds validation is not reference-sequence allele verification. No liftover is performed.

Gene identifiers, symbols and types come from cBioPortal. Full names and genomic gene locations remain absent. Tumour VAF is alternate reads / (alternate + reference reads); missing, sentinel or zero-total counts produce null. This is not population allele frequency.

## Source coverage
| Source | Data scope | State |
|---|---|---|
| [NCBI Gene](https://www.ncbi.nlm.nih.gov/gene/) | Full names and assembly-specific locations | Not retrieved |
| [ChEMBL](https://www.ebi.ac.uk/chembl/) | Compounds, targets, research evidence | Imported via Open Targets |
| [Reactome](https://reactome.org/) | Human gene-pathway memberships | Imported via Open Targets |

The genomic import does not itself supply drug/pathway records. Phase 5 adds the separately versioned Open Targets research snapshot below, retaining source attribution and retrieval times. No clinical conclusions are supplied. The separately versioned CellMiner snapshot below supplies drug-response measurements with coherent source z-score units and matched cell-line features.

## Import contract
Official APIs only. Preserve raw bytes and retrieval times. Verify every checksum before normalization. Reject inconsistent cohorts, assemblies and manifests. Classify invalid, excluded and duplicate rows separately. Reconcile downloaded = accepted + invalid + excluded + duplicates. Production promotion fails on invalid records. Import all rows atomically under an advisory transaction lock. Identical snapshots are no-ops; later snapshots preserve separate observation profiles.

Tests use explicitly synthetic fixtures in isolated, rolled-back schemas. They are never production seed data.

## Phase 5: Open Targets research associations

Imported a bounded ten-gene snapshot from https://api.platform.opentargets.org/api/v4/graphql on 2026-09-08. Target identifiers are resolved through official Ensembl REST symbol lookup. Open Targets supplies source-linked drug mechanisms, modality, historical maximum stage, research diseases, report identifiers/URLs and Reactome pathway memberships. Refresh is manual and versioned, aligned with source releases; the app does not query changing upstream data during analysis.

183 drugs, 186 target links, 220 pathways and 279 memberships. Manifest SHA: a203c4635eac2cdb679f4081c1163a730d70f78745b54f17b566ebf5b5c3b3cb. Raw requests and responses are committed; database reports record exclusions, invalid records and missing labels. Open Targets Platform data is CC0 1.0 with upstream source attribution preserved. See [licensing](backend/data/research_associations/SOURCE_LICENSE.md) and [research methods](docs/RESEARCH.md).

Source labels are not independently validated clinical findings. AACT trial entity labels include upstream LLM extraction, as documented by Open Targets. Report counts mix trials and other source records and do not quantify efficacy or independent studies. No response measurements, treatment ranking or variant-specific drug sensitivity is included.


## Phase 7: NCI CellMiner drug response

Imported a curated, aligned subset of [NCI CellMiner 2025.3](https://discover.nci.nih.gov/cellminer/) processed downloads. The source panel contains 60 diverse human cancer cell lines. Activity data are CellMiner DTP compound-activity average z scores; higher values mean greater sensitivity. Expression values are five-platform gene-transcript average z scores. Mutation values indicate a protein-function-affecting exome variant in the processed summary.

| Scope | Value |
|---|---|
| Cell lines | 60 |
| Expression measurements | 599 |
| Mutation-status measurements | 540 |
| Drug-response measurements | 593 |
| Selected genes | 10 |
| Predeclared FDA-status drugs | 10 |
| Curated CSV SHA-256 | `335d0bdb8bcb2f878acfe8250d886d225eaa559bc2d8635f59a0fc613b481acd` |

The manifest pins the original processed ZIP names, source dates and SHA-256 values. Ten drug names and one NSC per name were chosen before model evaluation. The ten genes inherit the existing PharmaGenome panel. Missing values stay missing; the absent STK11 row in the mutation source is never translated into a negative call.

NCI's reuse policy asks for National Cancer Institute credit, which is retained in the [source notice](backend/data/drug_response/SOURCE_LICENSE.md). CellMiner requests citation of Shankavaram et al. (BMC Genomics, 2009) and Reinhold et al. (Cancer Research, 2012). The software license does not relicense source data.

NCI-60 consists of immortalized cell lines, not patients. Its activity z scores are experimental research measurements, not clinical response labels, dose recommendations or treatment evidence. See [modeling methods](docs/MODELING.md).
