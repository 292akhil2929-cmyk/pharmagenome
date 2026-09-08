"""Bounded exploratory statistics with explicit methods and immutable source context."""
import hashlib
import json
import os
from datetime import UTC, datetime
from typing import Annotated, Literal

import numpy as np
import scipy
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from scipy import stats

from app import research

router = APIRouter(prefix="/api/statistics", tags=["Statistics"])
SEED = 20260908
RESAMPLES = 9999
Number = Annotated[float, Field(strict=True, ge=-1e12, le=1e12, allow_inf_nan=False)]
Group = Annotated[list[Number], Field(min_length=2, max_length=500)]


class MeasurementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    method: Literal["welch", "mann_whitney", "pearson", "spearman", "anova", "kruskal"]
    groups: Annotated[list[Group], Field(min_length=2, max_length=6)]
    unit: str = Field("unspecified units", min_length=1, max_length=60)


class ContingencyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    method: Literal["fisher", "chi_square"]
    table: list[list[Annotated[int, Field(strict=True, ge=0, le=1000000)]]] = Field(min_length=2, max_length=2)


class EnrichmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset_id: int | None = Field(None, strict=True, ge=1)
    genes: list[str] = Field(min_length=1, max_length=10)


def meta(method, parameters, inputs=None):
    result = {"method": method, "method_version": "1.0.0", "parameters": parameters,
              "computed_at": datetime.now(UTC).isoformat(), "code_revision": os.getenv("VERCEL_GIT_COMMIT_SHA", "development"),
              "software": {"scipy": scipy.__version__, "numpy": np.__version__},
              "alpha": 0.05, "limitations": [
                  "Exploratory research only. Statistical significance is not clinical importance or causality.",
                  "Assumptions and observation independence cannot be verified automatically.",
                  "A large p-value does not establish equivalence or prove the null hypothesis.",
              ]}
    if inputs is not None:
        result.update(inputs=inputs, input_sha256=hashlib.sha256(
            json.dumps(inputs, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest())
    return result


def finite(value):
    return float(value) if np.isfinite(value) else None


def describe(values):
    a = np.asarray(values, dtype=float)
    q = np.quantile(a, [0.25, 0.5, 0.75], method="linear")
    unique, counts = np.unique(a, return_counts=True)
    cumulative = np.cumsum(counts) / len(a)
    return {"n": len(a), "mean": float(a.mean()), "median": float(q[1]),
            "variance": float(a.var(ddof=1)), "standard_deviation": float(a.std(ddof=1)),
            "q1": float(q[0]), "q3": float(q[2]), "minimum": float(a.min()), "maximum": float(a.max()),
            "distribution": [{"value": float(v), "count": int(c), "cumulative_fraction": float(p)}
                             for v, c, p in zip(unique, counts, cumulative, strict=True)]}


def measurement(req):
    groups = [np.asarray(g, dtype=float) for g in req.groups]
    if req.method not in {"anova", "kruskal"} and len(groups) != 2:
        raise ValueError("This method requires exactly two groups/paired vectors.")
    if req.method in {"anova", "kruskal"} and len(groups) < 3:
        raise ValueError("Use at least three groups for this omnibus comparison.")
    a, b = groups[:2]
    result = meta(req.method, {"unit": req.unit, "alternative": "upper-tail omnibus" if req.method in {"anova", "kruskal"} else "two-sided",
                               "missing_values": "rejected; no deletion or imputation"},
                  {"groups": req.groups, "unit": req.unit})
    result["descriptive"] = [describe(g) for g in groups]
    result["limitations"].append("One unadjusted test per request; repeated exploratory tests require a prespecified correction plan.")
    ci, extra = None, {}
    if req.method == "welch":
        if a.var() == 0 and b.var() == 0:
            raise ValueError("Welch inference is undefined when both groups have zero variance.")
        test = stats.ttest_ind(a, b, equal_var=False)
        bounds = test.confidence_interval(confidence_level=0.95)
        ci = {"label": "95% CI for mean A minus mean B", "low": finite(bounds.low), "high": finite(bounds.high)}
        effect = {"label": "Mean A minus mean B", "value": float(a.mean() - b.mean())}
        null, alternative = "Population means are equal.", "Population means differ."
        assumptions = ["Independent observations and independent groups in comparable units.",
                       "Approximate normality within groups or adequate sample size; Welch allows unequal variances."]
        extra = {"degrees_of_freedom": finite(test.df)}
    elif req.method == "mann_whitney":
        tied = len(np.unique(np.concatenate(groups))) != len(a) + len(b)
        if min(len(a), len(b)) <= 8 and not tied:
            method = "exact"
        elif min(len(a), len(b)) < 10:
            method = stats.PermutationMethod(n_resamples=RESAMPLES, batch=128, rng=np.random.default_rng(SEED))
        else:
            method = "asymptotic"
        test = stats.mannwhitneyu(a, b, alternative="two-sided", method=method)
        label = method if isinstance(method, str) else "seeded permutation (exact when enumerable)"
        extra = {"p_value_method": label, "resamples": RESAMPLES if not isinstance(method, str) else None,
                 "seed": SEED if not isinstance(method, str) else None}
        effect = {"label": "Rank-biserial effect (positive: A tends higher)", "value": float(2 * test.statistic / (len(a) * len(b)) - 1)}
        null, alternative = "The two population distributions are identical.", "The distributions differ in the Mann–Whitney sense."
        assumptions = ["Independent observations and groups; ordinal or continuous measurements.",
                       "A location/median interpretation additionally requires comparable distribution shapes."]
    elif req.method in {"pearson", "spearman"}:
        if len(a) != len(b) or len(a) < 3:
            raise ValueError("Correlation requires equal-length paired vectors with at least three observations.")
        if np.ptp(a) == 0 or np.ptp(b) == 0:
            raise ValueError("Correlation is undefined for a constant vector.")
        if req.method == "pearson":
            test = stats.pearsonr(a, b)
            if len(a) >= 4:
                bounds = test.confidence_interval(confidence_level=0.95)
                ci = {"label": "95% Fisher-transform CI for Pearson r", "low": finite(bounds.low), "high": finite(bounds.high)}
            null, alternative = "Population linear correlation is zero.", "Population linear correlation is nonzero."
            assumptions = ["Independent paired observations; a meaningful linear relationship.",
                           "Pearson p-value/CI assumes an appropriate bivariate-normal model; outliers can dominate."]
        else:
            ra, rb = stats.rankdata(a), stats.rankdata(b)
            ra, rb = ra - ra.mean(), rb - rb.mean()
            scale = np.linalg.norm(ra) * np.linalg.norm(rb)

            def coefficient(x, axis=-1):
                return np.sum(x * rb, axis=axis) / scale

            test = stats.permutation_test((ra,), coefficient, permutation_type="pairings",
                                          alternative="two-sided", vectorized=True, n_resamples=RESAMPLES,
                                          batch=128, rng=np.random.default_rng(SEED))
            extra = {"p_value_method": "pairing permutation; exact if factorial(n) <= 9999, otherwise Monte Carlo",
                     "resamples": RESAMPLES, "seed": SEED}
            null, alternative = "Pairings are exchangeable under independence.", "A monotonic association departs from exchangeable pairings."
            assumptions = ["Independent paired observations; ordinal or continuous values; average ranks for ties.",
                           "Permutation inference requires exchangeability under the null; dependence or clusters invalidate it."]
        effect = {"label": "Pearson r" if req.method == "pearson" else "Spearman rho", "value": finite(test.statistic)}
    elif req.method == "anova":
        test = stats.f_oneway(*groups)
        all_values = np.concatenate(groups)
        total = float(np.sum((all_values - all_values.mean()) ** 2))
        between = sum(len(g) * (g.mean() - all_values.mean()) ** 2 for g in groups)
        effect = {"label": "Eta squared (between / total variation)", "value": finite(between / total) if total else None}
        null, alternative = "All population means are equal.", "At least one population mean differs."
        assumptions = ["Independent observations and groups; approximately normal residuals and equal population variances.",
                       "This is an omnibus test; it does not identify which group pairs differ."]
        extra = {"degrees_of_freedom": [len(groups) - 1, len(all_values) - len(groups)]}
    else:
        if min(map(len, groups)) < 5:
            raise ValueError("Kruskal–Wallis asymptotic inference requires at least five observations per group here.")
        test = stats.kruskal(*groups)
        n, k = sum(map(len, groups)), len(groups)
        effect = {"label": "Epsilon squared (clipped at zero)", "value": max(0.0, float((test.statistic - k + 1) / (n - k)))}
        null, alternative = "All group population distributions are identical.", "At least one distribution differs in rank location."
        assumptions = ["Independent observations; comparable distribution shapes for a median/location interpretation.",
                       "Tie-corrected asymptotic omnibus test; no pairwise post-hoc comparisons are performed."]
        extra = {"degrees_of_freedom": k - 1}
    if not np.isfinite(test.statistic) or not np.isfinite(test.pvalue):
        raise ValueError("The selected test is not estimable for these data. Check variation and group sizes.")
    result.update(statistic=float(test.statistic), p_value=float(test.pvalue), effect=effect, confidence_interval=ci,
                  null_hypothesis=null, alternative_hypothesis=alternative, assumptions=assumptions, details=extra,
                  interpretation="Evidence against the stated null at unadjusted alpha 0.05." if test.pvalue < .05 else
                  "Insufficient evidence against the stated null at unadjusted alpha 0.05.")
    return result


def contingency(req):
    if any(len(row) != 2 for row in req.table):
        raise ValueError("Supply a 2×2 count table.")
    table = np.asarray(req.table, dtype=np.int64)
    if np.any(table.sum(axis=0) == 0) or np.any(table.sum(axis=1) == 0):
        raise ValueError("Every row and column must have a positive total.")
    result = meta(req.method, {"alternative": "upper-tail" if req.method == "chi_square" else "two-sided", "correction": False}, {"table": req.table})
    expected = stats.contingency.expected_freq(table)
    if req.method == "chi_square":
        if np.any(expected < 5):
            raise ValueError("Expected cell counts below five: use Fisher exact for this table.")
        test = stats.chi2_contingency(table, correction=False)
        statistic, p = float(test.statistic), float(test.pvalue)
        effect = {"label": "Cramér V", "value": float(np.sqrt(statistic / table.sum()))}
    else:
        test = stats.fisher_exact(table, alternative="two-sided")
        statistic, p = finite(test.statistic), float(test.pvalue)
        effect = {"label": "Sample odds ratio (a×d / b×c)", "value": statistic,
                  "boundary": "positive infinity" if np.isinf(test.statistic) else None}
    result.update(statistic=statistic, p_value=p, effect=effect, confidence_interval=None, descriptive=[],
                  null_hypothesis="The two categorical variables are independent (odds ratio one).",
                  alternative_hypothesis="The categorical variables are associated (odds ratio differs from one).",
                  assumptions=["Independent observations; disjoint exhaustive categories; integer counts, not percentages.",
                               "Fisher conditions on margins; chi-square uses asymptotic inference without Yates correction."],
                  details={"expected_counts": expected.tolist(), "total": int(table.sum()),
                           "table_layout": "[[row1 outcome1, row1 outcome2], [row2 outcome1, row2 outcome2]]"},
                  interpretation="Evidence of association at unadjusted alpha 0.05." if p < .05 else
                  "Insufficient evidence of association at unadjusted alpha 0.05.")
    result["limitations"].append("No adjustment across repeated user-submitted tests; odds-ratio zero/infinity is a boundary estimate.")
    return result


def enrichment(gene_rows, pathways, selected):
    universe = {g["symbol"] for g in gene_rows}
    selected = set(selected)
    if not selected or selected - universe:
        raise ValueError("Select at least one gene, entirely within the imported research universe.")
    ids = {g["id"]: g["symbol"] for g in gene_rows}
    sets = {}
    for p in pathways:
        item = sets.setdefault(p["id"], {"id": p["id"], "name": p["name"], "genes": set()})
        item["genes"].add(ids[p["gene_id"]])
    rows = []
    for pid in sorted(sets):
        item = sets[pid]
        overlap = selected & item["genes"]
        N, K, n, k = len(universe), len(item["genes"]), len(selected), len(overlap)
        expected = n * K / N
        p = float(stats.hypergeom.sf(k - 1, N, K, n))
        rows.append({"id": pid, "name": item["name"], "overlap": k, "pathway_genes_in_universe": K,
                     "selected_genes": n, "universe_size": N, "genes": sorted(overlap),
                     "expected_overlap": expected, "fold_enrichment": k / expected,
                     "p_value": p, "url": "https://reactome.org/content/detail/" + pid})
    if rows:
        bh = stats.false_discovery_control([r["p_value"] for r in rows], method="bh")
        by = stats.false_discovery_control([r["p_value"] for r in rows], method="by")
        for row, qbh, qby in zip(rows, bh, by, strict=True):
            row.update(q_bh=float(qbh), q_by=float(qby))
    rows.sort(key=lambda r: (r["q_by"], r["p_value"], -r["overlap"], r["id"]))
    return rows


@router.post("/measurements")
def analyze_measurements(req: MeasurementRequest):
    try:
        return measurement(req)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/contingency")
def analyze_contingency(req: ContingencyRequest):
    try:
        return contingency(req)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/enrichment")
def analyze_enrichment(req: EnrichmentRequest):
    dataset, _, genes, _, pathways, _ = research.read_data(req.dataset_id)
    selected = sorted({g.strip().upper() for g in req.genes})
    try:
        rows = enrichment(genes, pathways, selected)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    result = meta("one-sided hypergeometric over-representation", {"selected_genes": selected,
                  "universe": sorted(g["symbol"] for g in genes), "corrections": ["Benjamini–Hochberg", "Benjamini–Yekutieli"],
                  "family_size": len(rows), "primary_correction": "BY"})
    result.update(dataset=dataset, rows=rows, tested_pathways=len(rows),
                  rejected_by=sum(r["q_by"] < .05 for r in rows), rejected_bh=sum(r["q_bh"] < .05 for r in rows),
                  null_hypothesis="Selected genes are a uniform random subset of the declared imported universe.",
                  alternative_hypothesis="A pathway contains more selected genes than expected under that null.",
                  assumptions=["Selection is independent of pathway membership under the null.",
                               "Universe and selected genes are fixed before testing; every imported pathway is in the test family."],
                  interpretation="Conditional exploratory test within the ten-gene source universe; not genome-wide enrichment.")
    result["limitations"] += [
        "The deliberately selected ten-gene import is a restricted, non-genome-wide universe; results are conditional on it.",
        "Choosing genes after inspecting pathway results invalidates confirmatory interpretation.",
        "All source pathways, including zero-overlap sets, are corrected together before ranking or pagination.",
        "BH assumes independent or suitably positively dependent tests. BY is the primary, more conservative correction for arbitrary dependence.",
        "Membership overlap and p-values do not establish pathway activation, causality or treatment relevance.",
    ]
    return result


@router.get("/options")
def analysis_options(dataset_id: int | None = Query(None, ge=1)):
    dataset, datasets, genes, _, pathways, _ = research.read_data(dataset_id)
    return {"dataset": dataset, "datasets": datasets, "genes": genes,
            "pathway_count": len({p["id"] for p in pathways})}
