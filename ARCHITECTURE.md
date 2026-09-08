# Architecture

## Phase 6: implemented scope
Next.js renders the public research workspace. Its server route proxies the read-only FastAPI system and dataset-report endpoints. FastAPI accesses PostgreSQL through parameterized psycopg queries. Dataset counts are live database counts, not sample fixture values. Descriptive genomic exploration and stateless sequence algorithms are implemented; drug-target/pathway associations and bounded statistical inference are implemented; drug-response ML remains planned.

```mermaid
flowchart LR
  Browser --> Next[Next.js on Vercel]
  Next --> API[FastAPI on Vercel]
  API --> PG[(PostgreSQL / Neon)]
  Import[Validated snapshot ingestion] --> PG
  PG --> Compute[Genomics / research overlap / enrichment]
  API --> Stats[Stateless statistical inference]
  API --> Sequence[Stateless DNA algorithms]
  Compute -.-> Explain[Optional result explanation]
```

## Repository
- frontend/app: App Router shell and server-side API proxy
- frontend/components: responsive scientific workspace and shadcn-derived controls
- backend/app: FastAPI API and database access
- backend/migrations: immutable SQL migrations
- backend/scripts: checksummed migration runner, official-source capture/replay and transactional importer
- backend/tests: health, validation and PostgreSQL constraint tests
- data/raw, processed, external, fixtures: future ingestion boundaries
- data_quality: validation policy
- docs: phased roadmap

## Database design
Genes use stable external numeric identifiers; symbols are searchable labels. Locations are separate and assembly-specific. A variant's unique key is assembly, chromosome, 1-based position, reference and alternate allele. Variants can overlap multiple genes.

Samples belong to studies and diseases. Molecular profiles record assay context; profile_samples includes unmutated samples and forms the future mutation-frequency denominator. profile_genes is available to specify targeted assay coverage. Importers must validate study/profile consistency and gene-level coverage. A missing observation is never automatically a confirmed negative result.

sample_variants carries sample-specific VAF, quality and source version. Population allele frequency and clinical interpretation are separately versioned annotations. VAF is not a population frequency.

Drug-target and drug-disease associations retain dataset versions and evidence. Drug response units, assay type and replicates remain explicit; no cross-assay comparison is implied.

Dataset versions have source, retrieval time, SHA-256 and fixture status. Ingestion reports reconcile downloaded = valid + invalid + excluded + duplicate records on successful runs. Analyses retain method version, parameters, results, source versions, random seed and code revision.

## Migration safety
The runner uses a PostgreSQL advisory transaction lock and one atomic transaction. Applied SQL is checksummed. Re-running is a no-op; modifying an applied migration raises an error. Add a new numbered migration for future changes. Migrations never execute during normal HTTP requests.

## Deployment
Two Vercel projects share one GitHub monorepo: pharmagenome (root frontend) and pharmagenome-api (root backend). Neon PostgreSQL connects only to the API. API_BASE_URL is server-only; the browser never receives DATABASE_URL.

FastAPI is supported by Vercel's Python runtime: https://vercel.com/docs/frameworks/backend/fastapi . Docker Compose supplies a separate PostgreSQL 17 environment for reproducible development. Redis/background workers are deferred until workload evidence requires them.

## Security and limitations
Read-only catalogue routes and bounded stateless sequence/statistics POST routes; bounded pagination and symbol input; SQL parameters; request IDs without secret logging; bounded database and HTTP timeouts; restrictive CORS. Public read access is limited to scientific catalog/system metadata. Sequence text uploads are bounded and not persisted to the application database. No clinical-data storage or arbitrary execution is exposed.
The platform is educational/research software. No clinical validity, AI explanations or model training is claimed.

The initial Vercel API build applies idempotent migrations in its trusted build environment. Subsequent schema releases should move migration execution to a controlled release job before traffic switches; do not use destructive migrations in preview builds.

## Snapshot ingestion
The committed cBioPortal LUAD snapshot retains all 566 profiled samples and a declared ten-gene SNV subset. Ensembl GRCh37 metadata supplies bounds. Capture preserves raw response bytes; replay validates the complete manifest and source IDs before Pydantic row validation, coordinate normalization and observation deduplication.

A transaction-scoped advisory lock serializes imports. Validation failures stop before writes; database failures roll back all writes. Successful import reports are stored with the same transaction. Rejected captures retain report evidence in the Actions artifact, not a partly populated production dataset.

Dataset SHA identifies an immutable import. Molecular profiles include the SHA so later imports retain their own sample observations. dataset_genes records source symbols/types and study_dataset_versions records each study/source-version relationship. Global variant identity remains assembly/locus/alleles; counts of global unique variants differ from versioned sample observations. Production blocks synthetic fixtures. No network capture, migration or mutation runs through public HTTP endpoints.

GET /api/datasets/{id}/report returns the source manifest, quality counts, rejection reasons and pipeline metadata. The frontend proxies fixed backend paths with bounded timeouts and displays download failures with retry. Database credentials remain server-only.

## Phase 3 genomic exploration
GET /api/genomics reads one completed snapshot and computes bounded descriptive results. The core separates eligible profiled samples from matching variant observations, preserves gene-specific denominators, deduplicates sample identities and returns explicit nulls for undefined frequencies. New dataset_variant_genes associations prevent future source versions from borrowing earlier consequences. The frontend uses Recharts charts adapted from shadcn registry examples, semantic tables and native filter controls. See [methods and API](docs/GENOMICS.md).

## Phase 4 sequence computation
POST /api/sequences/statistics and /api/sequences/align normalize and validate DNA, then compute without PostgreSQL. The frontend streams and bounds JSON request bodies before forwarding to fixed API paths. Inputs and scoring changes invalidate displayed results. Exports include normalized inputs, hashes, methods, parameters and code revision. See [sequence methods](docs/SEQUENCES.md).

## Phase 5 research associations
Migration 004 adds snapshot-scoped target identity, drug/pathway metadata, memberships, mechanisms, research disease labels and source report rows. Existing global identifiers remain stable; analysis queries use the versioned tables. A second pinned importer validates official Ensembl/Open Targets captures, then writes atomically under an advisory lock. GET /api/research computes distinct drugs, deduplicated report counts and independent pathway overlap. Public requests never mutate imported data. See [methods](docs/RESEARCH.md).

## Phase 6 statistical analysis

POST /api/statistics/measurements validates finite numerical groups and applies the declared test without missing-value deletion or imputation. POST /api/statistics/contingency validates integer 2 × 2 tables and guards sparse chi-square inference. These requests are not written to PostgreSQL. Responses include descriptive distributions, explicit hypotheses and assumptions, effect estimates, available intervals, input hashes, method/software versions and code revision.

GET /api/statistics/options returns the minimal source universe for one research snapshot. POST /api/statistics/enrichment reads immutable snapshot-scoped gene/pathway membership, tests every pathway with a one-sided hypergeometric upper tail, and applies BH and primary BY adjustment to the entire family before sorting. The ten-gene source universe is displayed and exported; results are conditional rather than genome-wide. See [statistical methods](docs/STATISTICS.md).
