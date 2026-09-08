# Statistical analysis methods

Phase 6 provides deterministic statistical calculations in FastAPI. The browser sends declared inputs to fixed analytical endpoints; the application does not store submitted measurement or contingency values in PostgreSQL. No LLM participates in these calculations.

## Measurement endpoint

`POST /api/statistics/measurements`

The request declares a method, two to six numerical groups, and a unit/context label. Each group accepts 2–500 finite numbers. Missing values, text, infinities and NaN are rejected rather than silently removed or imputed.

Every response reports group sample size, mean, median, sample variance and standard deviation (n − 1), linear-interpolated quartiles, range, and an exact empirical distribution table. One test is performed per request at unadjusted alpha 0.05.

| Method | Scope | Test statistic and effect | Inference |
|---|---|---|---|
| Welch t-test | Two independent groups | Welch t; mean A − B | Two-sided p-value and 95% confidence interval for the mean difference |
| Mann–Whitney U | Two independent groups | U; rank-biserial effect | Two-sided exact calculation for small untied data, seeded permutation for small tied data, otherwise asymptotic |
| Pearson correlation | Two equal-length paired vectors, n ≥ 3 | r | Two-sided p-value; 95% Fisher-transform interval when n ≥ 4 |
| Spearman correlation | Two equal-length paired vectors, n ≥ 3 | rho from average ranks | Two-sided pairing permutation, exact when all permutations fit within 9,999 and seeded Monte Carlo otherwise |
| One-way ANOVA | Three to six independent groups | F; eta squared | Upper-tail omnibus p-value |
| Kruskal–Wallis | Three to six independent groups with at least five observations each | tie-corrected H; epsilon squared clipped at zero | Upper-tail asymptotic omnibus p-value |

The response states its null and alternative hypotheses, assumptions, estimator meaning, confidence interval availability, software versions, method version, code revision, computation time, normalized input and SHA-256. A large p-value is described as insufficient evidence against the null, not evidence of equivalence. Statistical significance is not equated with clinical importance or causality.

## Contingency endpoint

`POST /api/statistics/contingency`

The request contains a 2 × 2 table of non-negative integer counts. Rows and columns must each have a positive total.

Fisher's exact test reports a two-sided p-value and the sample odds ratio. Boundary estimates serialize as a textual boundary with a JSON null, never infinity or NaN. Pearson chi-square uses no Yates correction, reports Cramér V, and is rejected when any expected count is below five. Expected counts and the declared table orientation are included.

## Pathway enrichment endpoint

`POST /api/statistics/enrichment`

This performs one-sided hypergeometric over-representation against the imported research snapshot. The universe is exactly the ten source genes in that snapshot. It is deliberately restricted and cannot be interpreted as genome-wide enrichment.

For every imported Reactome pathway, including zero-overlap pathways:

- N is the ten-gene imported universe.
- K is the pathway size inside that universe.
- n is the number of selected genes.
- k is the observed overlap.
- Raw p is P(X ≥ k) under the hypergeometric null.
- Fold enrichment is k / (nK/N).

The complete family is adjusted before sorting or pagination. Benjamini–Hochberg and Benjamini–Yekutieli q-values are both returned; BY is primary because pathway sets overlap and arbitrary dependency is possible. The output preserves all tested pathways, the selected/universe genes, snapshot ID, retrieval time, SHA-256, software versions, code revision and limitations.

The null assumes the selected genes are a uniform random subset of the declared universe and that selection is independent of pathway membership. Choosing genes after inspecting results invalidates confirmatory interpretation. Membership and enrichment do not establish pathway activity, causality, treatment relevance or drug response.

## Reproducibility

The JSON export contains every submitted value for user-supplied analyses, or the complete source snapshot reference and result family for enrichment. It also contains parameters, input/source SHA-256, method/software versions, timestamp, code revision, hypotheses, assumptions and limitations.

The computation uses SciPy 1.18.0 and NumPy 2.3.3. Seeded permutation procedures use seed 20260908 and at most 9,999 resamples. Results should be independently reproduced from the exported inputs and declared versions before publication.
