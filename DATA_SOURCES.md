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

## Remaining sources
| Source | Planned data | State |
|---|---|---|
| [NCBI Gene](https://www.ncbi.nlm.nih.gov/gene/) | Full names and assembly-specific locations | Not retrieved |
| [ChEMBL](https://www.ebi.ac.uk/chembl/) | Compounds, targets, research evidence | Not retrieved |
| [Reactome](https://reactome.org/) | Human gene-pathway memberships | Not retrieved |

Record release, license and attribution before adding these sources. No drug/pathway records or clinical conclusions are supplied by the current import. Drug-response and ML modules remain gated on usable data, coherent units and defensible group-aware evaluation.

## Import contract
Official APIs only. Preserve raw bytes and retrieval times. Verify every checksum before normalization. Reject inconsistent cohorts, assemblies and manifests. Classify invalid, excluded and duplicate rows separately. Reconcile downloaded = accepted + invalid + excluded + duplicates. Production promotion fails on invalid records. Import all rows atomically under an advisory transaction lock. Identical snapshots are no-ops; later snapshots preserve separate observation profiles.

Tests use explicitly synthetic fixtures in isolated, rolled-back schemas. They are never production seed data.
