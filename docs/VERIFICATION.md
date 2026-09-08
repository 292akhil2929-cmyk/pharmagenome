# Phase 2 verification

Verified application commit: 4f55299991528c38d0c89e9220f2f9253e896b10.

- [GitHub Actions](https://github.com/292akhil2929-cmyk/pharmagenome/actions/runs/34201910098): success.
- Backend: Ruff passed; 39 tests passed against PostgreSQL 17; backend Docker image built.
- Frontend: TypeScript and production build passed; 7 Playwright tests passed.
- Ingestion tests cover field validation, exclusions, duplicate conflicts, missing VAF, incomplete cohorts, pinned real snapshot replay, checksum tampering, manifest scope, transactional rollback, idempotency, snapshot history and production fixture rejection.
- Browser cases cover empty/unavailable/recovery, synthetic populated states, provenance, JSON downloads and download failure/retry, dark-mode persistence, desktop/mobile overflow, keyboard drawer focus/Escape/restore.
- Production frontend and backend reached Vercel Ready. API readiness reports 002_ingestion.
- Anonymous live system response: 566 samples, 506 distinct variants, 10 genes, 0 drugs, 0 pathways.
- Live import report: 966 downloaded = 839 accepted + 127 excluded + 0 invalid + 0 duplicate observations. All 127 exclusions are non-SNV.
- Frontend report proxy returned HTTP 200, JSON provenance and the expected attachment header; raw snapshot link points to immutable import commit 678c250817dd7bc024671e79d057578d399fa014.
- Anonymous HTML and all eight referenced JS/CSS assets returned 200.
- Live in-app browser confirmed actual populated cohort, provenance and dark mobile view. At 390px there was no page overflow; captured console error list was empty.
- Independent finish review found no material frontend defects in source and 1440px/390px populated/provenance screenshots; its conditional CI requirement is satisfied by the successful run above.

## Evidence boundaries
CI screenshots use explicitly synthetic populated fixtures; live database counts were verified separately. Chrome connection timed out twice during this final pass, so live checks used the in-app browser. Its download-event observer timed out; the download interaction passed in Chromium CI and the live report endpoint/attachment response was independently verified. Do not describe this as a confirmed saved download in the in-app browser.

[Public source capture workflow](https://github.com/292akhil2929-cmyk/pharmagenome/actions/runs/34200468520) completed successfully. Raw bytes, manifest and reconciliation report are committed in backend/data/luad_snv. Production data is real public source data, not the browser fixtures.

This release implements ingestion and provenance, not genomic-frequency explorers, sequence algorithms, statistics, drug response, ML or AI explanation. Ten selected genes and SNVs are the explicit scope. No clinical validity is claimed. Full Docker Compose runtime remains untested end-to-end; its backend image and PostgreSQL integration checks passed.
