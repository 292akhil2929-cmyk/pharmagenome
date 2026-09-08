# Phase 7 verification

Verified application commit: c17926609e0a7aef7a63d9f95e25dac9490813e4.

- [GitHub Actions run 34251633271](https://github.com/292akhil2929-cmyk/pharmagenome/actions/runs/34251633271): success.
- Backend: Ruff passed; 137 tests passed against PostgreSQL 17; backend Docker image built.
- Frontend: TypeScript and production build passed; 26 Playwright tests passed.
- CellMiner snapshot tests pin the curated SHA-256, reconcile 60 cells, 599 expression values, 540 mutation-status values and 593 drug responses, preserve STK11 mutation as unavailable, and verify all ten chosen drug records have FDA-approved source status.
- Modeling reference tests independently check the predeclared zero z-score target, deterministic 5-fold × 3-repeat predictions, exactly three held-out predictions per sample, class balance, a 0.5 prior-baseline ROC-AUC, confusion-matrix reconciliation, predictor allowlisting and duplicate rejection.
- PostgreSQL integration tests cover atomic idempotent import, dataset provenance, ten drugs, eleven predictor options, mutation-group eligibility, the real 59-measurement Erlotinib path, complete predictions and unknown-drug rejection.
- Browser tests cover 1440px and 390px response/model states, request construction, result focus, metric and confusion evidence, complete JSON export, feature-count guard, API error recovery and page containment.
- Browser fixtures are explicitly synthetic UI evidence. Scientific counts and values below come from the live imported source.

## Live dataset and API

Both Vercel projects reached Ready. The live health endpoint returned version 0.7.0. Readiness reported migration `005_drug_response_modeling`; system state reported Phase 7, 626 total samples, 193 drugs, 10 genes, 506 variants and 220 pathways.

The live modeling options endpoint returned CellMiner version `cellminer-2025.3-curated-v1`, ten drugs, eleven selectable predictors and eight mutation genes with at least three cell lines in each comparison group. Dataset SHA-256 is `335d0bdb8bcb2f878acfe8250d886d225eaa559bc2d8635f59a0fc613b481acd`.

A live Erlotinib/TP53 comparison returned 59 measured cell lines, 29 mutation-present and 30 no-called-mutation values, with unadjusted Mann–Whitney p = 0.7386871647. This value is a deployment check, not a biological claim.

All three live estimators completed and returned 177 held-out predictions for 59 measured cell lines. With the full eleven-feature request and the predeclared zero boundary, there were 27 positive and 32 comparison cell lines. Logistic regression returned mean fold ROC-AUC 0.4879894, random forest 0.4210582 and histogram gradient boosting 0.4476190; the shared prior baseline was 0.5. These are internal panel results and are not a model-selection or efficacy claim. Returned code revisions matched the deployed commits.

## Live browser and responsive inspection

Chrome loaded the deployed CellMiner manifest, all ten drug options, all eleven predictors and the real TP53 response distribution. Running the full eleven-feature logistic model completed and moved focus to Evaluation ledger. The interface exposed fold mean and standard deviation, prior baselines, pooled held-out ROC, confusion matrix, permutation importance, complete JSON export and the clinical-use boundary.

Fresh live Chrome captures at 1440px and 390px reported document scroll width exactly equal to viewport width. A first inspection found the metric ledger could overflow at an intermediate app-panel width; commit `53f7ddb` added the breakpoint. The final `c179266` recapture also exposed the retrieval date, separated the predictor summary and gave F1 the complete last responsive row. The independent finish reviewer returned `ship` with no visible regressions.

## Scientific and reproducibility boundaries

NCI-60 contains immortalized cancer cell lines rather than patients. Activity values are CellMiner experimental z scores. The binary target uses a predeclared activity z-score boundary of zero, independent of held-out outcomes; it is not a clinical response threshold. Five-fold cross-validation repeated three times estimates performance within this small panel; it is not external validation.

Imputation and logistic scaling are fitted inside each training fold. Response values and identifiers are outside the predictor allowlist. The models use fixed hyperparameters and no tuning search. The prior dummy classifier uses identical splits. Pooled ROC and confusion values duplicate each cell line across three repeats and are descriptive; the fold standard deviations are not independent confidence intervals.

Permutation importance is computed only on held-out fold data. It has no effect direction, can share credit among correlated predictors and can be negative through sampling noise. Mutation comparison labels say “no called mutation” because absence in the processed summary does not prove wild type. No result supports diagnosis, treatment choice, dosing, safety or patient benefit.

## Previous functionality retained

The Phase 6 statistical suite, Phase 5 source-linked associations, sequence tools, genomic explorers, ingestion constraints and browser flows pass in the same CI run. The TCGA LUAD snapshot remains 566 cohort samples, 839 accepted observations and 506 unique SNVs. The Open Targets snapshot remains 183 source-linked drugs and 220 pathways; CellMiner adds ten separate NSC drug identities and 60 separate study samples.
