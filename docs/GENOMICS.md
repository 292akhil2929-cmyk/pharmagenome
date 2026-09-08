# Descriptive genomics

## Scope and method
Phase 3 explores the imported ten-gene GRCh37 SNV subset from TCGA LUAD. It does not expand the source scope or infer clinical effects.

For each gene:
```text
frequency = distinct matching sample IDs / distinct eligible profiled sample IDs
```
Eligibility comes from profile_samples joined to profile_genes in the selected dataset. Study and disease filters restrict that cohort. Gene, chromosome, variant type and literal search restrict matching observations without shrinking the denominator. A zero denominator returns null, displayed as Not estimable. Minimum mutated sample count filters the ranking and matrix rows only.

Counting units:
- Unique variants: distinct assembly/locus/ref/alt identities.
- Observations: distinct sample–variant pairs within the dataset.
- Matching samples: distinct samples with any selected observation.
- Gene frequency numerator: each sample counted once per gene, regardless of its variant count.

Multiple profiles do not double-count a sample. Conflicting VAF values for the same sample–variant pair across profiles become missing; no arbitrary profile is selected. Per-gene eligibility can differ from the overall cohort. [cBioPortal describes gene-panel-aware frequency denominators](https://docs.cbioportal.org/user-guide/faq/#why-are-some-samples-not-profiled-for-certain-genes).

All accepted source SNVs are included, including silent consequences when supplied. These descriptive frequencies may differ from cBioPortal's default alteration query, which can apply consequence restrictions and include other alteration types. They are not population prevalence.

## Endpoint
`GET /api/genomics` (the frontend proxies this same path).

| Parameter | Meaning |
|---|---|
| dataset_id | One completed dataset; defaults to latest genomic snapshot |
| study / disease | Source study identifier / internal disease ID from options |
| gene | Exact source symbol, case-insensitive |
| chromosome | Canonical 1–22, X, Y, MT |
| variant_type | Imported SNV, MNV, insertion, deletion or complex |
| q | Literal case-insensitive substring of source symbol or chr:position:ref>alt |
| min_samples | Minimum matching sample count for gene ranking/matrix only |
| sort | position, position_desc, samples; deterministic genomic tie-break |
| page / page_size | Variant page, 1–100 rows; out-of-range pages clamp |
| heatmap_page | Matrix page of 40 cohort samples |

Responses include dataset checksum, source, selected parameters, calculation method, code revision, timestamp, summary, ranked genes, variant page, count distributions and matrix page. JSON exports explicitly state that variant and matrix records are paginated; aggregate counts and distributions cover the full filtered result. No AI service is invoked.

Each database read is capped at 50,000 records per relation. Larger datasets fail with an explicit batch-analysis-required response instead of truncating results. This implementation intentionally fits the bounded MVP snapshot.

## Visual interpretation
- Frequency chart spans 0–100% and has a corresponding exact-value table and keyboard-accessible gene filter buttons.
- Chromosome counts are not length-normalized density.
- Variant-type composition covers imported types only; excluded indels do not appear as observed zeroes.
- VAF histogram uses sample tumour read fractions, not population allele frequency. Ten half-open bins cover [0,1), with the final bin including 1. Missing values are counted separately.
- Mutation matrix shows matching observations; empty cells are not proof of wild type. An em dash denotes absent imported gene coverage. Samples are ordered by public coded identifier, 40 per page.
- Gene chromosome labels describe observed variant loci, not genomic gene coordinates.
- Full gene names/locations, clinical significance, population allele frequencies, pathways and drug targets are unavailable until separately sourced.

## Snapshot preservation
Migration 003 adds dataset_variant_genes and backfills Phase 2 associations from its existing observation/gene mappings. Future imports write associations under their own dataset ID; explorer queries do not draw annotations from other snapshots. Migration 003 preserves the original Phase 2 data and checksummed migrations.

## Reference result
For snapshot `aae580bb94295d59dfa7e18676fd7ce62547881958bd0919169f0b1bcc1ca78f`, TP53 has 267 matching samples / 566 profiled samples (47.1731%), with 181 distinct SNVs. This is a dataset-specific descriptive result, not a disease-risk estimate.
