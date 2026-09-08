# Phase 3 verification

Verified application commit: 70adedaf4f38a3f7229381760339203b40f9993e.

- [GitHub Actions run 34203642122](https://github.com/292akhil2929-cmyk/pharmagenome/actions/runs/34203642122): success.
- Backend: Ruff passed, 56 tests passed with PostgreSQL 17; Docker image built.
- Frontend: TypeScript and production build passed; 11 Playwright tests passed.
- New backend coverage: distinct sample numerator, full and gene-specific eligible denominator, cohort versus variant filters, empty cohort null frequency, missing/discordant VAF, histogram endpoint 1.0, literal search, sorting, pagination, profile deduplication, snapshot isolation and invalid API parameters.
- Pinned public snapshot was imported into an isolated test schema and queried through FastAPI. TP53 result: 267 / 566, 181 unique SNVs; pagination leaves summary unchanged. Tests roll back the isolated schema.
- New browser coverage: genomic chart/table rendering, inline gene and variant details, explicit missing metadata, JSON exports, filters, pagination, no-match result, service failure/recovery, dedicated explorer navigation, mobile overflow and reduced-motion dark captures.
- Independent finish review: ship; explicit filter labels and settled dark 1440px/390px screenshots confirmed. Scientific computation was verified separately from the fixture screenshots.

## Live verification
The live public API returned 566 eligible samples, 459 matching samples, 506 unique SNVs, 839 sample–variant observations and 10 affected genes. The TP53 query returned 267 matching samples, 181 unique variants and frequency 267/566.

Live API checks confirmed no overlapping variant IDs between two consecutive TP53 pages, unchanged cohort denominator across those pages, 566 eligible samples retained for an empty variant search, and 40 coded samples on matrix page 2.

Chrome verified the populated Genomics view, TP53 filter, 47.2% display with numerator and denominator, variant page 2, dedicated explorer navigation and mobile dark rendering. Settled mobile page width remained within the viewport; captured console error list was empty.

JSON export download events passed in Chromium CI. The desktop browser tool's live download observer timed out, so a saved live browser download is not claimed. Live source data and calculation responses were independently inspected.

## Evidence boundaries
Browser screenshots use explicitly synthetic test fixtures; they are layout/interaction evidence, not scientific data. Actual counts above come from the pinned public source snapshot and live/API integration checks.

This release supports descriptive genomics only within the ten-gene GRCh37 SNV subset. It does not provide full gene metadata, clinical annotation, population frequency, inferential statistics, sequence algorithms, drug response, ML or AI explanations. All accepted SNVs are included; this is not necessarily cBioPortal's default consequence-filtered alteration query. See [methods](GENOMICS.md) and [source provenance](../DATA_SOURCES.md).

Full Docker Compose runtime is not verified end-to-end; PostgreSQL integration tests and the backend Docker build passed.
