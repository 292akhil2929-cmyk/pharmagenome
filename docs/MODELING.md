# Drug-response modeling

## Source and scope

Phase 7 uses an immutable curated view of NCI CellMiner 2025.3. It aligns the same NCI-60 cell-line columns across:

- DTP compound-activity average z scores;
- five-platform RNA expression average z scores for the established ten-gene PharmaGenome panel;
- protein-function-affecting exome variant summaries for that panel.

Ten named FDA-status drugs were fixed before evaluation: Erlotinib, Gefitinib, Cisplatin, Paclitaxel, Doxorubicin, Vemurafenib, Trametinib, Osimertinib, Crizotinib and Sunitinib. One NSC record is retained per name. The selected genes were already fixed by the genomic workspace. This prevents presenting a post-hoc best-performing drug or feature set as if it were prespecified.

The curated CSV SHA-256 is `335d0bdb8bcb2f878acfe8250d886d225eaa559bc2d8635f59a0fc613b481acd`. Its manifest pins the three upstream ZIP SHA-256 values and source dates. Missing source fields remain null. In particular, the processed mutation table contains no STK11 row, so PharmaGenome does not turn that absence into a wild-type call.

## Response comparison

`GET /api/modeling/response` compares a selected drug's measured activity between cell lines with and without a called protein-function-affecting mutation for one eligible gene. It reports both group sizes, medians, quartiles, every cell-line point, a two-sided Mann–Whitney U p-value and rank-biserial effect.

“Higher” means greater sensitivity in the CellMiner activity z-score convention. “No called mutation” means no mutation in this processed summary; it does not prove a wild-type genotype. Each request is one unadjusted exploratory comparison. Users exploring many drug–gene pairs need a prespecified multiplicity plan.

## Prediction target

`POST /api/modeling/evaluate` creates a binary teaching target for one drug:

- positive: activity z score strictly above the independently pinned zero boundary;
- negative: activity z score at or below zero.

The zero boundary is declared from CellMiner's standardized activity metric before evaluation and does not use held-out outcomes. It is a modeling convention, not a clinical response threshold.

Available predictors are the ten expression z scores plus a count of called protein-function-affecting mutations among the nine genes with source mutation rows. Response values and sample identifiers cannot be predictors. Users select at least two unique declared features.

## Evaluation protocol

Three fixed models are available:

- L2-regularized logistic regression;
- random forest with 200 trees, depth 3 and minimum leaf size 3;
- histogram gradient boosting with 100 iterations, at most 7 leaves and L2 regularization.

All use class balancing. No hyperparameter search selects a favorable result. Evaluation uses 5-fold stratified cross-validation repeated 3 times with seed `20260908`. Median imputation and, for logistic regression, standardization are fitted inside each training fold. Every reported probability comes from a test fold. The same cell line appears once per repeat, giving three held-out predictions per cell line.

The response reports mean and standard deviation across 15 folds for accuracy, balanced accuracy, precision, recall, F1 and ROC-AUC. A prior-probability dummy classifier runs through the same splits. The confusion matrix and ROC curve pool the repeated held-out predictions; repeats are correlated, so they are visualization summaries rather than independent observations.

Feature importance is the mean held-out ROC-AUC decrease after five permutations per feature in every fold. It has no effect direction, may share credit among correlated predictors, and can be negative through sampling noise.

## Reproducibility

Every evaluation response includes the dataset SHA-256, exact drug, ordered feature list, algorithm, split parameters, random seed, software versions, code revision, input hash, all pooled predictions, metrics, baseline, ROC coordinates, confusion matrix, permutation importance and limitations. The frontend JSON export retains the complete response.

## Limits

NCI-60 is a small heterogeneous panel of immortalized cell lines, not patients. Repeated cross-validation estimates internal discrimination in this panel; it is not an external validation set. The interface makes no drug recommendation, patient prediction, dose claim or treatment ranking. Performance and feature importance do not establish causality or clinical benefit.
