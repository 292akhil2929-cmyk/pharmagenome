import math
import os

import pytest
from fastapi.testclient import TestClient

from app import modeling
from app.ingestion import load, load_modeling
from app.ingestion.modeling import GENES, replay
from app.main import app
from tests.test_ingestion_db import isolated_database  # noqa: F401

client = TestClient(app)


def synthetic_records(n=40):
    rows = []
    for i in range(n):
        value = float(i - n / 2)
        row = {"cell_line": f"TEST:{i:02d}", "tissue": "TEST", "responses": {"NSC:1": value},
               "mutation_count": i % 4}
        for j, gene in enumerate(GENES):
            row[f"expression_{gene}"] = value / n + (j % 3) * .01
        rows.append(row)
    return rows


def test_pinned_cellminer_snapshot_replays_and_reconciles():
    manifest, data = replay()
    assert manifest["sha256"] == "335d0bdb8bcb2f878acfe8250d886d225eaa559bc2d8635f59a0fc613b481acd"
    assert data["report"] == {"downloaded": 60, "valid": 60, "invalid": 0, "duplicates": 0,
                              "excluded": 0, "cell_lines": 60, "expression": 599,
                              "mutation": 540, "response": 590}
    assert len({r["cell_line"] for r in data["records"]}) == 60
    assert all(r["features"]["STK11"]["mutation"] is None for r in data["records"])
    assert all(d["fda_status"] == "FDA approved" for d in manifest["drugs"])


def test_repeated_cv_is_deterministic_and_uses_only_held_out_predictions():
    features = ["expression_EGFR", "expression_KRAS", "mutation_count"]
    first = modeling.evaluate(synthetic_records(), "NSC:1", "logistic", features)
    second = modeling.evaluate(synthetic_records(), "NSC:1", "logistic", features)
    assert first == second
    assert first["n"] == 40
    assert first["class_counts"] == {"more_sensitive": 20, "less_sensitive_or_equal": 20}
    assert len(first["predictions"]) == 120
    assert {(p["repeat"], p["fold"]) for p in first["predictions"]} == {
        (repeat, fold) for repeat in range(1, 4) for fold in range(1, 6)}
    assert first["metrics"]["roc_auc"]["mean"] > .95
    assert first["baseline_metrics"]["roc_auc"]["mean"] == pytest.approx(.5)
    assert sum(sum(row) for row in first["confusion_matrix"]) == 120
    assert all(math.isfinite(p["probability"]) for p in first["predictions"])


@pytest.mark.parametrize("features", [["response_NSC:1", "expression_EGFR"],
                                      ["expression_EGFR", "expression_EGFR"]])
def test_leakage_and_duplicate_features_are_rejected(features):
    with pytest.raises(ValueError):
        modeling.evaluate(synthetic_records(), "NSC:1", "logistic", features)


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="PostgreSQL required")
@pytest.mark.usefixtures("isolated_database")
def test_database_import_idempotency_and_modeling_api(monkeypatch):
    monkeypatch.setattr(load_modeling, "connection", load.connection)
    monkeypatch.setattr(modeling, "connection", load.connection)
    manifest, data = replay()
    imported = load_modeling.load_validated(manifest, data)
    assert load_modeling.load_validated(manifest, data)["status"] == "already_loaded"
    options = client.get("/api/modeling/options").json()
    assert options["dataset"]["id"] == imported["dataset_id"]
    assert len(options["drugs"]) == 10
    assert len(options["features"]) == 11
    assert {g["gene"] for g in options["mutation_groups"]} >= {"BRAF", "KRAS", "TP53"}
    response = client.get("/api/modeling/response", params={
        "drug_id": "NSC:718781", "gene": "EGFR"}).json()
    assert len(response["points"]) == 59
    assert response["direction"] == "Higher means greater sensitivity"
    result = client.post("/api/modeling/evaluate", json={
        "drug_id": "NSC:718781", "algorithm": "logistic",
        "features": ["expression_EGFR", "expression_KRAS", "mutation_count"]})
    assert result.status_code == 200
    body = result.json()
    assert body["dataset"]["sha256"] == manifest["sha256"]
    assert body["n"] == 59
    assert len(body["predictions"]) == 177
    assert body["parameters"]["cross_validation"]["folds"] == 5
    assert body["input_sha256"]
    assert client.post("/api/modeling/evaluate", json={
        "drug_id": "NSC:999999", "features": ["expression_EGFR", "mutation_count"]}).status_code == 404
