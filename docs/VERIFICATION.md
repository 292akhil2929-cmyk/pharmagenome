# Verification evidence

## Phase 9 analytical dashboard

Verified implementation commit: `eba18b93196952a5b467e73c3e797e2178530477`.

- [GitHub Actions run 34303847610](https://github.com/292akhil2929-cmyk/pharmagenome/actions/runs/34303847610): success.
- Backend: Ruff passed; 141 tests passed against PostgreSQL 17; backend Docker image built.
- Frontend: TypeScript and production build passed; 33 Playwright tests passed.
- Dashboard browser tests cover real-response rendering, chart scope labels, drug-target evidence, browser-local recent-analysis metadata, failure recovery, the Research Assistant boundary and navigation at 1440 px, 700 px and 390 px.
- Live Vercel API reports version 0.9.0, Phase 9, database status ready and migration `005_drug_response_modeling`.
- Live inventory reports 626 samples, 506 variants, 10 genes, 193 drugs and 220 pathways. These are database table counts across imported datasets; the genomic cohort remains 566 eligible samples.
- Live browser inspection confirmed all four evidence views, complete purpose-named navigation, the honest unavailable `gpt-6-astra` state and light/dark appearance.
- A live 653 px inspection found 98 px of horizontal overflow at the previous 650 px drawer boundary. Commit `ea690d6` raised the responsive boundary to 760 px; the deployed recheck reported a 653 px viewport, a 643 px document width and the mobile drawer.
- Recent-analysis history is browser-local metadata only. Raw measurements, contingency cells, gene selections, cell-line points and prediction rows are excluded.

## Phase 8 explanation integration

Verified application commit: `a651cee7c2074e5b334f524ed7faef2add6aa528`.

- [GitHub Actions run 34255566590](https://github.com/292akhil2929-cmyk/pharmagenome/actions/runs/34254481171): success.
- Backend: Ruff passed; 141 tests passed against PostgreSQL 17; backend Docker image built.
- Frontend: TypeScript and production build passed; 28 Playwright tests passed.
- Backend tests cover missing-key behavior, request-bound evidence validation, exact model/request settings, structured claim references and rejection of an invented numeric claim.
- Browser tests verify compact evidence construction, omission of raw inputs, the explanation action, rendered evidence keys, recoverable model-status failure and focus return to the underlying result.
- Production reports version 0.8.0 and Phase 8. The explanation status names `gpt-6-astra` and returns `available: false`; a direct POST returns 503 because no server-side OpenAI API key is configured.
- Live Chrome executed the real statistics flow at 1440px and 390px. The computed result retained focus, the unavailable explanation state was visible, and document scroll width equaled viewport width at both sizes.
- The deployed UI does not claim a generated answer. Core statistics, modeling, exports and provenance remain usable without an LLM.

## Phase 7 verification

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
