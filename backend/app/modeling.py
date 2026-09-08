"""Leakage-aware exploratory drug-response modeling for the pinned NCI-60 panel."""
import hashlib
import json
import os
from datetime import UTC, datetime
from typing import Literal

import numpy as np
import scipy
import sklearn
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from scipy import stats
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.db import connection
from app.ingestion.load_modeling import DATASET

router = APIRouter(prefix="/api/modeling", tags=["Drug-response modeling"])
SEED = 20260908
TARGET_THRESHOLD = 0.0
GENES = ["BRAF", "EGFR", "KRAS", "MET", "NF1", "PIK3CA", "RB1", "STK11", "TP53", "KEAP1"]
FEATURES = [f"expression_{g}" for g in GENES] + ["mutation_count"]
ALGORITHMS = {"logistic": "Regularized logistic regression", "random_forest": "Random forest",
              "gradient_boosting": "Histogram gradient boosting"}


class ModelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset_id: int | None = Field(None, strict=True, ge=1)
    drug_id: str = Field(min_length=5, max_length=30, pattern=r"^NSC:[0-9]+$")
    algorithm: Literal["logistic", "random_forest", "gradient_boosting"] = "logistic"
    features: list[str] = Field(default_factory=lambda: FEATURES.copy(), min_length=2, max_length=len(FEATURES))


def metadata(method, parameters, inputs):
    digest = hashlib.sha256(json.dumps(
        inputs, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return {"method": method, "method_version": "1.0.0", "parameters": parameters,
            "computed_at": datetime.now(UTC).isoformat(),
            "code_revision": os.getenv("VERCEL_GIT_COMMIT_SHA", "development"),
            "software": {"scikit_learn": sklearn.__version__, "numpy": np.__version__, "scipy": scipy.__version__},
            "inputs": inputs, "input_sha256": digest}


def read_panel(dataset_id=None):
    with connection() as conn:
        datasets = conn.execute("""SELECT d.id,d.name,d.version,d.sha256,d.retrieved_at,d.is_fixture,
            d.manifest,s.name AS source,s.url FROM dataset_versions d JOIN sources s ON s.id=d.source_id
            WHERE d.name=%s AND EXISTS (SELECT 1 FROM ingestion_runs r WHERE r.dataset_id=d.id
            AND r.status='succeeded') ORDER BY d.retrieved_at DESC,d.id DESC""", (DATASET,)).fetchall()
        dataset = next((d for d in datasets if dataset_id is None or d["id"] == dataset_id), None)
        if not dataset:
            raise HTTPException(404, "No completed CellMiner modeling snapshot found.")
        drugs = conn.execute("""SELECT drug_id AS id,name,drug_class AS mechanism,maximum_stage AS status
            FROM dataset_drugs WHERE dataset_id=%s ORDER BY name""", (dataset["id"],)).fetchall()
        responses = conn.execute("""SELECT s.id AS sample_id,s.sample_identifier AS cell_line,s.tissue,
            r.drug_id,r.response_value FROM drug_responses r JOIN samples s ON s.id=r.sample_id
            WHERE r.dataset_id=%s ORDER BY s.sample_identifier,r.drug_id""", (dataset["id"],)).fetchall()
        feature_rows = conn.execute("""SELECT f.sample_id,g.gene_symbol,f.feature_type,f.feature_value
            FROM cell_line_features f JOIN genes g ON g.id=f.gene_id WHERE f.dataset_id=%s""",
                                    (dataset["id"],)).fetchall()
    records = {}
    for row in responses:
        record = records.setdefault(row["sample_id"], {"sample_id": row["sample_id"], "cell_line": row["cell_line"],
                                                      "tissue": row["tissue"], "responses": {}})
        record["responses"][row["drug_id"]] = row["response_value"]
    for row in feature_rows:
        record = records.get(row["sample_id"])
        if not record:
            continue
        if row["feature_type"] == "expression_z_score":
            record[f"expression_{row['gene_symbol']}"] = row["feature_value"]
        elif row["feature_value"] == 1:
            record["mutation_count"] = record.get("mutation_count", 0) + 1
            record.setdefault("mutated_genes", []).append(row["gene_symbol"])
        else:
            record.setdefault("mutation_count", 0)
    return dataset, datasets, drugs, list(records.values())


def estimator(algorithm):
    if algorithm == "logistic":
        model = LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000, random_state=SEED)
        return Pipeline([("impute", SimpleImputer(strategy="median")),
                         ("scale", StandardScaler()), ("model", model)])
    if algorithm == "random_forest":
        model = RandomForestClassifier(n_estimators=200, max_depth=3, min_samples_leaf=3,
                                       class_weight="balanced", random_state=SEED, n_jobs=1)
    else:
        model = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=7, min_samples_leaf=5,
                                               l2_regularization=1, class_weight="balanced", random_state=SEED)
    return Pipeline([("impute", SimpleImputer(strategy="median")), ("model", model)])


def score(y, predicted, probability):
    return {"accuracy": accuracy_score(y, predicted), "balanced_accuracy": balanced_accuracy_score(y, predicted),
            "precision": precision_score(y, predicted, zero_division=0),
            "recall": recall_score(y, predicted, zero_division=0),
            "f1": f1_score(y, predicted, zero_division=0), "roc_auc": roc_auc_score(y, probability)}


def evaluate(records, drug_id, algorithm, features):
    unknown = sorted(set(features) - set(FEATURES))
    if unknown or len(set(features)) != len(features):
        raise ValueError("Features must be unique members of the declared modeling panel.")
    usable = [r for r in records if drug_id in r["responses"]]
    if len(usable) < 30:
        raise ValueError("At least 30 response measurements are required.")
    y_cont = np.array([r["responses"][drug_id] for r in usable], dtype=float)
    threshold = TARGET_THRESHOLD
    y = (y_cont > threshold).astype(int)
    if min(np.bincount(y)) < 10:
        raise ValueError("The predeclared z-score classes are too small for five-fold stratification.")
    X = np.array([[r.get(feature, np.nan) for feature in features] for r in usable], dtype=float)
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)
    pipe, dummy = estimator(algorithm), DummyClassifier(strategy="prior")
    predictions, fold_metrics, baseline_metrics, importances = [], [], [], []
    for index, (train, test) in enumerate(cv.split(X, y)):
        fitted = clone(pipe).fit(X[train], y[train])
        probability = fitted.predict_proba(X[test])[:, 1]
        predicted = (probability >= .5).astype(int)
        dfit = clone(dummy).fit(X[train], y[train])
        dprob = dfit.predict_proba(X[test])[:, 1]
        dpred = (dprob >= .5).astype(int)
        fold_metrics.append(score(y[test], predicted, probability))
        baseline_metrics.append(score(y[test], dpred, dprob))
        pi = permutation_importance(fitted, X[test], y[test], scoring="roc_auc", n_repeats=5,
                                    random_state=SEED + index)
        importances.append(pi.importances_mean)
        repeat, fold = divmod(index, 5)
        for pos, sample_index in enumerate(test):
            predictions.append({"cell_line": usable[sample_index]["cell_line"], "repeat": repeat + 1,
                                "fold": fold + 1, "actual": int(y[sample_index]),
                                "predicted": int(predicted[pos]), "probability": float(probability[pos])})
    def summarize(items):
        return {key: {"mean": float(np.mean([m[key] for m in items])),
                      "standard_deviation": float(np.std([m[key] for m in items], ddof=1))}
                for key in items[0]}
    actual = np.array([p["actual"] for p in predictions])
    probability = np.array([p["probability"] for p in predictions])
    predicted = np.array([p["predicted"] for p in predictions])
    fpr, tpr, thresholds = roc_curve(actual, probability)
    importance = np.mean(importances, axis=0)
    order = np.argsort(-importance)
    return {"threshold": threshold, "n": len(usable), "class_counts": {"more_sensitive": int(y.sum()),
            "less_sensitive_or_equal": int(len(y) - y.sum())}, "metrics": summarize(fold_metrics),
            "baseline_metrics": summarize(baseline_metrics),
            "confusion_matrix": confusion_matrix(actual, predicted, labels=[0, 1]).tolist(),
            "roc_curve": [{"false_positive_rate": float(a), "true_positive_rate": float(b),
                           "threshold": None if not np.isfinite(c) else float(c)}
                          for a, b, c in zip(fpr, tpr, thresholds, strict=True)],
            "importance": [{"feature": features[i], "mean_decrease_roc_auc": float(importance[i]),
                            "direction": "magnitude only; permutation importance has no effect direction"}
                           for i in order], "predictions": predictions}


@router.get("/options")
def options(dataset_id: int | None = Query(None, ge=1)):
    dataset, datasets, drugs, records = read_panel(dataset_id)
    eligible = {gene: sum(gene in r.get("mutated_genes", []) for r in records) for gene in GENES}
    return {"dataset": dataset, "datasets": datasets, "drugs": drugs, "features": FEATURES,
            "algorithms": [{"id": key, "name": value} for key, value in ALGORITHMS.items()],
            "mutation_groups": [{"gene": gene, "mutated": count, "wild_type": len(records) - count}
                                for gene, count in eligible.items() if count >= 3 and len(records) - count >= 3],
            "protocol": {"cross_validation": "5 folds × 3 repeats, stratified, seed 20260908",
                         "target": "Activity z score above the independently pinned zero threshold",
                         "positive_class": "more sensitive",
                         "pipeline": "Median imputation and scaling fit inside each training fold"}}


@router.get("/response")
def response(drug_id: str = Query(pattern=r"^NSC:[0-9]+$"), gene: str = Query(min_length=2, max_length=20),
             dataset_id: int | None = Query(None, ge=1)):
    dataset, _, drugs, records = read_panel(dataset_id)
    if drug_id not in {d["id"] for d in drugs} or gene.upper() not in GENES:
        raise HTTPException(404, "Drug or gene is outside the selected snapshot.")
    gene = gene.upper()
    points = [{"cell_line": r["cell_line"], "tissue": r["tissue"], "value": r["responses"][drug_id],
               "group": "mutation present" if gene in r.get("mutated_genes", []) else "no called mutation"}
              for r in records if drug_id in r["responses"]]
    groups = [[p["value"] for p in points if p["group"] == label]
              for label in ("mutation present", "no called mutation")]
    if min(map(len, groups)) < 3:
        raise HTTPException(422, "Both mutation groups require at least three measured cell lines.")
    test = stats.mannwhitneyu(groups[0], groups[1], alternative="two-sided", method="asymptotic")
    return {"dataset": dataset, "drug": next(d for d in drugs if d["id"] == drug_id), "gene": gene,
            "metric": "CellMiner compound activity average z score", "direction": "Higher means greater sensitivity",
            "groups": [{"label": label, "n": len(values), "median": float(np.median(values)),
                        "q1": float(np.quantile(values, .25)), "q3": float(np.quantile(values, .75))}
                       for label, values in zip(("mutation present", "no called mutation"), groups, strict=True)],
            "test": {"method": "two-sided Mann–Whitney U, asymptotic tie correction",
                     "statistic": float(test.statistic), "p_value": float(test.pvalue),
                     "effect": float(2 * test.statistic / (len(groups[0]) * len(groups[1])) - 1)},
            "points": points, "limitations": [
                "Unadjusted exploratory comparison; testing many drug–gene pairs requires multiplicity control.",
                "No-called-mutation includes only this processed exome summary and does not prove wild type.",
                "Cell-line association does not establish causality, clinical response, or treatment suitability."]}


@router.post("/evaluate")
def evaluate_model(req: ModelRequest):
    dataset, _, drugs, records = read_panel(req.dataset_id)
    if req.drug_id not in {d["id"] for d in drugs}:
        raise HTTPException(404, "Drug is outside the selected snapshot.")
    try:
        result = evaluate(records, req.drug_id, req.algorithm, req.features)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    inputs = {"dataset_sha256": dataset["sha256"], "drug_id": req.drug_id,
              "algorithm": req.algorithm, "features": req.features}
    result.update(metadata(ALGORITHMS[req.algorithm], {
        "cross_validation": {"folds": 5, "repeats": 3, "stratified": True, "seed": SEED},
        "target": "activity z score > 0 (predeclared independently of outcomes)", "target_threshold": TARGET_THRESHOLD, "decision_threshold": .5,
        "imputation": "median fit within each training fold", "class_weight": "balanced",
        "importance": "held-out permutation decrease in ROC-AUC, five shuffles per fold"}, inputs))
    result.update(dataset=dataset, drug=next(d for d in drugs if d["id"] == req.drug_id),
                  algorithm=req.algorithm, features=req.features,
                  interpretation="Repeated cross-validation estimates discrimination inside this small cell-line panel; it is not external validation.",
                  limitations=[
                      "NCI-60 is small and heterogeneous; repeated folds are correlated and metric standard deviations are descriptive.",
                      "The zero z-score boundary is predeclared from the source metric and is not a clinical response threshold.",
                      "No hyperparameter search was performed; the fixed models were specified before comparison.",
                      "Permutation importance can share credit among correlated features and does not give causal direction.",
                      "Performance is not evidence of patient benefit and must not guide treatment."])
    return result
