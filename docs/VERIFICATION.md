# Phase 5 verification

Verified application commit: 5e5ed40275d874c3829209cb6b25e48037411f62.

- [GitHub Actions run 34236752371](https://github.com/292akhil2929-cmyk/pharmagenome/actions/runs/34236752371): success.
- Backend: Ruff passed, 110 tests passed with PostgreSQL 17; backend Docker image built.
- Frontend: TypeScript and production build passed; 19 Playwright tests passed.
- Public-source pipeline tests reconcile 186 target links, verify raw/manifest SHA, reject mismatched/truncated source data, and validate EGFR's 82 drugs and 37 pathways through PostgreSQL and FastAPI.
- Tests cover idempotency, older-snapshot preservation, scoped keys, unmapped mechanisms, unsafe links, conflicting duplicates, distinct report counts, literal search, filter independence and pagination.
- New browser tests cover source disclosure, detail panels, disease/report links, JSON downloads, gene selection, pending filters, empty results, error/retry, drug/pathway paging and mixed-source report semantics.
- Four settled 1440px/390px light/dark screenshots passed independent finish review: ship, with no blocking issues within the new research view.
- Browser screenshot fixtures are explicitly synthetic and do not establish scientific findings.

## Live verification
Both Vercel projects reached Ready after deploying the application commit. Public API/system responses report 566 samples, 506 unique SNVs, 10 genes, 183 drugs and 220 pathways.

Research snapshot:
- SHA a203c4635eac2cdb679f4081c1163a730d70f78745b54f17b566ebf5b5c3b3cb.
- Retrieved 2026-09-08T13:52:07.254788Z.
- 186 downloaded candidate rows, 186 accepted target links, zero invalid/excluded/duplicate rows.
- 279 gene-pathway memberships; 1,052 unmapped disease-label occurrences counted separately.

EGFR selection returned 82 drugs/target links and 37 pathways. Consecutive drug pages contained disjoint IDs. A no-match drug query returned zero drugs while retaining the same 37 pathways. GEFITINIB returned CHEMBL939, an EGFR mechanism and 347 distinct source report records. These records are not independent studies or evidence of efficacy.

Chrome verified Gene explorer to EGFR research navigation, filtering, actual mechanism/report details, report page 2, mixed-source quality labels, dark mode and mobile containment. Settled mobile content width was 380px within a 390px viewport. Desktop rendering was checked at the live 1280px viewport in addition to CI's 1440px captures.

## Previous functionality retained
The genomic snapshot SHA remains aae580bb94295d59dfa7e18676fd7ce62547881958bd0919169f0b1bcc1ca78f. Live TP53 results remain 267 / 566 matching samples, 181 distinct SNVs and 281 observations. The sequence global-alignment teaching case still returns score 12. Existing sequence reference and genomic integration tests pass in the same suite.

## Evidence boundaries
The application performs deterministic filtering, counts and overlap without an LLM. Open Targets documents upstream LLM extraction of some AACT trial drug/disease labels; those source assignments are preserved and not independently validated here.

JSON downloads passed in Chromium CI; a saved live Chrome download is not claimed. Full Docker Compose runtime is not verified end-to-end; PostgreSQL integration tests and the backend Docker build passed.

This release provides gene-level research associations and descriptive pathway overlap. It does not provide enrichment statistics, clinical interpretation, variant-specific sensitivity, drug-response modeling, ML or AI explanations. See [research methods](RESEARCH.md), [genomic methods](GENOMICS.md) and [sequence methods](SEQUENCES.md).
