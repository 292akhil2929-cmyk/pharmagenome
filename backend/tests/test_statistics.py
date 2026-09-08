import itertools
import json
import math
import os

import pytest
from fastapi.testclient import TestClient

from app import research
from app.ingestion import load, load_associations
from app.ingestion.associations import replay
from app.main import app
from app.statistics import MeasurementRequest, describe, enrichment, measurement
from tests.test_ingestion_db import isolated_database  # noqa: F401

client = TestClient(app)


def calculate(method, groups):
    return measurement(MeasurementRequest(method=method, groups=groups))


def test_descriptive_sample_denominator_and_interpolation():
    d = describe([1, 2, 3, 4])
    assert d["mean"] == d["median"] == 2.5
    assert d["variance"] == pytest.approx(5 / 3)
    assert d["standard_deviation"] == pytest.approx(math.sqrt(5 / 3))
    assert (d["q1"], d["q3"]) == (1.75, 3.25)
    assert describe([1, 1, 2])["distribution"] == [
        {"value": 1, "count": 2, "cumulative_fraction": 2 / 3},
        {"value": 2, "count": 1, "cumulative_fraction": 1}]


def test_welch_equal_variance_analytic_reference_and_swap():
    a, b = [1, 2, 3, 4, 5], [4, 5, 6, 7, 8]
    r = calculate("welch", [a, b])
    assert r["statistic"] == pytest.approx(-3)
    assert r["details"]["degrees_of_freedom"] == pytest.approx(8)
    assert r["p_value"] == pytest.approx(0.0170716812337826)
    assert r["effect"]["value"] == -3
    assert r["confidence_interval"]["low"] == pytest.approx(-5.306004135204166)
    assert r["confidence_interval"]["high"] == pytest.approx(-0.693995864795834)
    swapped = calculate("welch", [b, a])
    assert swapped["p_value"] == r["p_value"]
    assert swapped["effect"]["value"] == 3
    assert r["input_sha256"] != swapped["input_sha256"]


def test_mann_whitney_exact_extreme_and_ties_permutation():
    r = calculate("mann_whitney", [[1, 2, 3], [4, 5, 6]])
    assert r["statistic"] == 0
    assert r["p_value"] == pytest.approx(2 / math.comb(6, 3))
    assert r["effect"]["value"] == -1
    tied = calculate("mann_whitney", [[1, 1, 2], [2, 3, 3]])
    again = calculate("mann_whitney", [[1, 1, 2], [2, 3, 3]])
    assert tied["p_value"] == again["p_value"]
    assert "permutation" in tied["details"]["p_value_method"]


def test_pearson_and_exact_spearman_with_ties():
    r = calculate("pearson", [[1, 2, 3, 4], [8, 6, 4, 2]])
    assert r["effect"]["value"] == pytest.approx(-1)
    assert r["p_value"] == pytest.approx(0)
    a, b = [1, 2, 3, 4], [1, 2, 2, 4]
    r = calculate("spearman", [a, b])
    # Enumerate the 24 labelled pairings independently using known average ranks.
    ranks_b = [1, 2.5, 2.5, 4]
    def corr(x):
        return sum((v - 2.5) * (w - 2.5) for v, w in zip(x, ranks_b)) / math.sqrt(5 * 4.5)
    observed = corr(a)
    null = [corr(p) for p in itertools.permutations(a)]
    expected = min(1, 2 * min(sum(v >= observed - 1e-12 for v in null),
                             sum(v <= observed + 1e-12 for v in null)) / len(null))
    assert r["effect"]["value"] == pytest.approx(observed)
    assert r["p_value"] == pytest.approx(expected)


def test_omnibus_analytic_reference_and_rank_invariance():
    r = calculate("anova", [[1, 2, 3], [2, 3, 4], [3, 4, 5]])
    assert r["statistic"] == pytest.approx(3)
    assert r["p_value"] == pytest.approx(0.125)
    assert r["effect"]["value"] == pytest.approx(0.5)
    groups = [[1, 3, 5, 7, 9], [2, 4, 6, 8, 10], [11, 12, 13, 14, 15]]
    r = calculate("kruskal", groups)
    transformed = calculate("kruskal", [[x ** 3 for x in g] for g in groups])
    assert r["statistic"] == pytest.approx(12 / (15 * 16) * (25 ** 2 / 5 + 30 ** 2 / 5 + 65 ** 2 / 5) - 3 * 16)
    assert r["p_value"] == transformed["p_value"]


@pytest.mark.parametrize("method,groups", [
    ("welch", [[1, 1], [2, 2]]), ("pearson", [[1, 1, 1], [1, 2, 3]]),
    ("spearman", [[1, 2, 3], [1, 2]]), ("anova", [[1, 2], [3, 4]]),
    ("kruskal", [[1, 2], [3, 4], [5, 6]]), ("anova", [[1, 1], [1, 1], [1, 1]]),
    ("welch", [[1, 2], [3, 4], [5, 6]]),
])
def test_undefined_data_rejected(method, groups):
    assert client.post("/api/statistics/measurements", json={"method": method, "groups": groups}).status_code == 422


@pytest.mark.parametrize("groups", [[[1], [2, 3]], [["1", 2], [3, 4]], [[True, 2], [3, 4]],
                                    [[1e13, 2], [3, 4]], [[1] * 501, [2, 3]]])
def test_input_bounds_and_types(groups):
    assert client.post("/api/statistics/measurements", json={"method": "welch", "groups": groups}).status_code == 422


def test_fisher_published_reference_and_infinite_odds_serialization():
    r = client.post("/api/statistics/contingency", json={"method": "fisher", "table": [[6, 2], [1, 4]]}).json()
    assert r["statistic"] == 12
    assert r["p_value"] == pytest.approx(0.10256410256410256)
    r = client.post("/api/statistics/contingency", json={"method": "fisher", "table": [[5, 0], [0, 5]]}).json()
    assert r["effect"]["boundary"] == "positive infinity"
    assert r["statistic"] is None
    json.dumps(r, allow_nan=False)


def test_chi_square_expected_counts_reference_and_sparse_guard():
    r = client.post("/api/statistics/contingency", json={"method": "chi_square", "table": [[20, 10], [10, 20]]}).json()
    assert r["statistic"] == pytest.approx(20 / 3)
    assert r["effect"]["value"] == pytest.approx(1 / 3)
    assert r["details"]["expected_counts"] == [[15, 15], [15, 15]]
    for table in [[[1, 2], [3, 4]], [[0, 0], [3, 4]], [[1, 2, 3], [4, 5, 6]], [[1.1, 2], [3, 4]]]:
        assert client.post("/api/statistics/contingency", json={"method": "chi_square", "table": table}).status_code == 422


def test_hypergeometric_and_full_family_adjustment_by_hand():
    genes = [{"id": i, "symbol": str(i)} for i in range(10)]
    pathways = [{"id": pid, "name": pid, "gene_id": i} for pid, ids in
                [("A", [0, 1]), ("B", [0]), ("C", [9])] for i in ids]
    rows = {r["id"]: r for r in enrichment(genes, pathways, ["0", "1"])}
    assert rows["A"]["p_value"] == pytest.approx(1 / math.comb(10, 2))
    assert rows["B"]["p_value"] == pytest.approx(0.2)
    assert rows["C"]["p_value"] == 1
    assert rows["A"]["q_bh"] == pytest.approx(3 / 45)
    assert rows["B"]["q_bh"] == pytest.approx(0.3)
    assert rows["A"]["q_by"] == pytest.approx((3 / 45) * (1 + 1 / 2 + 1 / 3))
    assert rows["A"]["fold_enrichment"] == 5
    assert all(r["p_value"] == 1 for r in enrichment(genes, pathways, [str(i) for i in range(10)]))
    with pytest.raises(ValueError):
        enrichment(genes, pathways, ["OUTSIDE"])


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="PostgreSQL required")
@pytest.mark.usefixtures("isolated_database")
def test_source_enrichment_family_and_snapshot_provenance(monkeypatch):
    monkeypatch.setattr(load_associations, "connection", load.connection)
    monkeypatch.setattr(research, "connection", load.connection)
    manifest, data = replay()
    imported = load_associations.load_validated(manifest, data)
    options = client.get("/api/statistics/options").json()
    assert len(options["genes"]) == 10
    r = client.post("/api/statistics/enrichment", json={"genes": [" egfr ", "EGFR"], "dataset_id": imported["dataset_id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["dataset"]["sha256"] == manifest["sha256"]
    assert body["tested_pathways"] == len(body["rows"]) == 220
    assert sum(row["overlap"] > 0 for row in body["rows"]) == 37
    assert all(row["q_by"] >= row["q_bh"] >= row["p_value"] - 1e-12 for row in body["rows"])
    assert body["parameters"]["selected_genes"] == ["EGFR"]
    assert client.post("/api/statistics/enrichment", json={"genes": ["OUTSIDE"]}).status_code == 422
    assert client.post("/api/statistics/enrichment", json={"genes": ["EGFR"], "dataset_id": 99999999}).status_code == 404
