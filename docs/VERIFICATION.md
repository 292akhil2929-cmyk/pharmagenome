# Phase 6 verification

Verified application commit: f65885480a52e78dba561f8b86406fbe293edb56.

- [GitHub Actions run 34242373011](https://github.com/292akhil2929-cmyk/pharmagenome/actions/runs/34242373011): success.
- Backend: Ruff passed; 132 tests passed against PostgreSQL 17; backend Docker image built.
- Frontend: TypeScript and production build passed; 23 Playwright tests passed.
- Backend reference tests cover descriptive sample denominators and quartile interpolation, Welch analytic values and swap symmetry, exact/permutation Mann–Whitney, Pearson, exact-enumerated Spearman with ties, ANOVA, monotonic-transform Kruskal invariance, Fisher boundary serialization, chi-square expected counts and sparse-table rejection.
- Enrichment tests independently verify a hypergeometric probability and hand-calculated BH/BY adjustments, include zero-overlap pathways in the family, and confirm 220 source pathways through PostgreSQL and FastAPI.
- Bounds tests reject missing, non-finite, non-numeric, Boolean, oversized and too-small inputs. Production/CI dependency manifest parity is tested so Vercel includes NumPy and SciPy.
- Browser tests cover keyboard tabs, loading/error/retry states, stale-result clearing, strict numeric parsing, all analysis forms, expected-count and descriptive tables, empirical-distribution and paired plots, full JSON downloads, pathway paging, BY-first labels, responsive containment and dark mode.
- Browser captures use explicit synthetic teaching/interface fixtures. They establish layout and interaction evidence, not scientific findings.

## Statistical reference results

The backend reference suite checks Welch t = -3, df = 8, p = 0.0170716812, mean difference -3 and 95% CI [-5.306004, -0.693996] for [1,2,3,4,5] versus [4,5,6,7,8]. It checks Fisher's two-sided p = 0.1025641026 and odds ratio 12 for [[6,2],[1,4]], plus chi-square = 6.666667 and Cramér V = 1/3 for [[20,10],[10,20]].

The Spearman tie test independently enumerates all 24 labeled pairings. Hypergeometric and false-discovery tests are compared with hand calculations rather than only reusing the implementation under test.

## Live verification

Both Vercel projects reached Ready. Anonymous frontend HTML returned the expected PharmaGenome title and all eight referenced CSS/JavaScript assets returned HTTP 200. Chrome verified the deployed statistical workbench at 390px: the result page width was 380px, two ECDF panels rendered, and the Welch teaching result displayed t = -3 and p = 0.0170717 without errors.

Direct live API checks completed successfully for Mann–Whitney, Pearson, Spearman, ANOVA, Kruskal–Wallis, Fisher exact and chi-square. Their returned code revision matched the deployed Phase 6 release.

The live options endpoint returned research dataset 2, ten genes, 220 pathways and snapshot SHA a203c4635eac2cdb679f4081c1163a730d70f78745b54f17b566ebf5b5c3b3cb. A live EGFR enrichment request and Chrome result used all 220 pathways, reported zero BY q < 0.05, showed the declared ten-gene universe, and retained hypotheses, assumptions, correction rationale and source provenance. Twenty rows appeared on the first page while the JSON response retained the complete family.

## Finish review

An independent Impeccable review checked 1440px and 390px light/dark statistics, correlation and enrichment captures. Its first pass found two screenshot-fixture truth issues: a Spearman capture inherited Welch wording, and enrichment combined a disconnected status with a database-backed claim. Both fixtures were corrected and recaptured. The verdict pass scored both fixes resolved and returned `ship`. Its scope was visual/interaction/scientific-copy consistency; the numerical and deployment claims above come from CI and live checks.

## Previous functionality retained

The genomic snapshot SHA remains aae580bb94295d59dfa7e18676fd7ce62547881958bd0919169f0b1bcc1ca78f. Live system inventory remains 566 samples, 506 unique SNVs, 10 genes, 183 drugs and 220 pathways. Existing genomic, sequence and research-association tests pass in the same suite. The sequence global-alignment teaching case remains score 12; EGFR remains 82 drugs and 37 overlapping pathways in the research explorer.

## Evidence boundaries

Measurement and contingency inputs are submitted to FastAPI and are not persisted to the application database; exported JSON contains them. Statistical results are exploratory and do not establish clinical importance, equivalence, causality or treatment effect.

Enrichment is conditional on the deliberately selected ten-gene imported universe. It is not genome-wide. Pathway overlap and adjusted p-values do not establish pathway activation, causality, treatment relevance or drug response. BY is primary because overlapping pathway tests may be dependent; BH is reported secondarily.

No drug-response dataset, machine-learning model, clinical prediction or AI explanation is included in Phase 6. Full Docker Compose runtime is not claimed; PostgreSQL integration and the backend Docker build passed.
