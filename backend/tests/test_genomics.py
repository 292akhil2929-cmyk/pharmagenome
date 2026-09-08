import copy
import os

import pytest
from fastapi.testclient import TestClient

from app import genomics
from app.genomics import compute
from app.ingestion import load
from app.ingestion.normalize import normalize
from app.main import app
from tests.fixtures_ingestion import fixture_manifest, fixture_payload
from tests.test_ingestion_db import isolated_database  # noqa: F401

client = TestClient(app)


def example():
    members = [
        {"profile_id": "p", "sample_id": 1, "sample_identifier": "A", "study_id": "study-a", "disease_id": 1},
        {"profile_id": "p", "sample_id": 2, "sample_identifier": "B", "study_id": "study-a", "disease_id": 1},
        {"profile_id": "p", "sample_id": 3, "sample_identifier": "C", "study_id": "study-b", "disease_id": 2},
    ]
    genes = [{"id": 7157, "symbol": "TP53", "gene_type": "protein-coding", "profile_id": "p"},
             {"id": 1956, "symbol": "EGFR", "gene_type": "protein-coding", "profile_id": "p"}]
    base = {"profile_id": "p", "assembly": "GRCh37", "chromosome": "17", "ref": "A",
            "alt": "T", "variant_type": "SNV", "vaf": 0.5}
    obs = [{**base, "sample_id": 1, "variant_id": 1, "position": 100},
           {**base, "sample_id": 1, "variant_id": 2, "position": 200, "vaf": None},
           {**base, "sample_id": 3, "variant_id": 1, "position": 100, "vaf": 1.0}]
    links = [{"variant_id": 1, "gene_id": 7157, "consequence": "Missense"},
             {"variant_id": 2, "gene_id": 7157, "consequence": "Missense"}]
    return members, genes, obs, links


def test_frequency_uses_distinct_samples_and_retains_zero_observation_members():
    result = compute(*example())
    tp53, egfr = result["genes"]
    assert (tp53["mutated_samples"], tp53["eligible_samples"], tp53["frequency"]) == (2, 3, 2 / 3)
    assert (egfr["mutated_samples"], egfr["eligible_samples"], egfr["frequency"]) == (0, 3, 0)
    assert result["summary"]["observations"] == 3
    assert result["summary"]["variants"] == 2
    assert result["heatmap"]["rows"][0]["values"] == [1, 0, 1]


def test_variant_filters_do_not_shrink_denominator_and_cohort_filters_do():
    result = compute(*example(), disease="1", q="17:100", gene="TP53")
    assert result["genes"][0]["frequency"] == 0.5
    assert result["summary"]["eligible_samples"] == 2
    empty = compute(*example(), chromosome="7")
    assert empty["summary"]["variants"] == 0
    assert empty["genes"][0]["eligible_samples"] == 3
    assert empty["genes"][0]["frequency"] == 0


def test_zero_cohort_is_undefined_not_zero_and_minimum_is_ranking_only():
    empty = compute(*example(), study="missing")
    assert all(g["frequency"] is None for g in empty["genes"])
    assert empty["summary"]["eligible_samples"] == 0
    filtered = compute(*example(), min_samples=3)
    assert filtered["genes"] == []
    assert filtered["summary"]["variants"] == 2


def test_vaf_missing_and_one_endpoint_histogram():
    result = compute(*example())
    assert sum(x["count"] for x in result["vaf_histogram"]) == 2
    assert result["vaf_histogram"][-1]["count"] == 1
    assert result["summary"]["missing_vaf"] == 1
    assert result["variants"]["items"][0]["population_allele_frequency"] is None


def test_pagination_sort_search_and_page_clamp():
    first = compute(*example(), page_size=1, sort="position_desc")
    assert first["variants"]["items"][0]["position"] == 200
    last = compute(*example(), page_size=1, page=99)
    assert last["variants"]["page"] == 2
    assert compute(*example(), q="tp53")["variants"]["total"] == 2
    assert compute(*example(), q="%")["variants"]["total"] == 0


def test_coverage_is_gene_specific_and_duplicate_profiles_do_not_inflate_counts():
    members, genes, obs, links = example()
    genes[1]["profile_id"] = "uncovered"
    members.append({**members[0], "profile_id": "p2"})
    genes.append({**genes[0], "profile_id": "p2"})
    obs.append({**obs[0], "profile_id": "p2", "vaf": 0.2})
    result = compute(members, genes, obs, links)
    assert result["genes"][0]["frequency"] == 2 / 3
    assert result["genes"][1]["frequency"] is None
    assert result["summary"]["observations"] == 3
    assert result["summary"]["missing_vaf"] == 2


@pytest.mark.parametrize("query", [
    "page=0", "page_size=101", "min_samples=-1", "dataset_id=0", "chromosome=chr17",
    "variant_type=bad", "sort=arbitrary", "heatmap_page=0", "q=" + "x" * 81,
])
def test_api_rejects_invalid_filters(query):
    assert client.get("/api/genomics?" + query).status_code == 422


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="PostgreSQL required")
@pytest.mark.usefixtures("isolated_database")
def test_api_snapshot_scope_and_pagination(monkeypatch):
    monkeypatch.setattr(genomics, "connection", load.connection)
    data = normalize(fixture_payload())
    first = load.load_validated(fixture_manifest(), data)
    later = copy.deepcopy(data)
    later["observations"] = []
    later["report"] = {**later["report"], "valid": 0, "downloaded": 0, "unique_variants": 0}
    second = load.load_validated({**fixture_manifest(), "sha256": "c" * 64}, later)
    original = client.get("/api/genomics", params={"dataset_id": first["dataset_id"], "page_size": 1})
    assert original.status_code == 200
    body = original.json()
    assert body["summary"]["eligible_samples"] == 2
    assert body["summary"]["variants"] == 1
    assert body["genes"][0]["frequency"] == 0.5
    assert body["dataset"]["is_fixture"] is True
    newer = client.get("/api/genomics", params={"dataset_id": second["dataset_id"]}).json()
    assert newer["summary"]["variants"] == 0
    assert newer["summary"]["eligible_samples"] == 2
    assert client.get("/api/genomics?dataset_id=99999999").status_code == 404


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="PostgreSQL required")
@pytest.mark.usefixtures("isolated_database")
def test_pinned_public_snapshot_end_to_end(monkeypatch):
    monkeypatch.setattr(genomics, "connection", load.connection)
    imported = load.load_snapshot()
    response = client.get("/api/genomics", params={"dataset_id": imported["dataset_id"], "gene": "TP53"})
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["eligible_samples"] == 566
    assert body["summary"]["mutated_samples"] == 267
    assert body["summary"]["variants"] == 181
    assert body["genes"][0]["frequency"] == 267 / 566
    assert body["dataset"]["sha256"] == "aae580bb94295d59dfa7e18676fd7ce62547881958bd0919169f0b1bcc1ca78f"
    page = client.get("/api/genomics", params={"dataset_id": imported["dataset_id"],
                                             "gene": "TP53", "page": 2, "page_size": 10}).json()
    assert page["summary"] == body["summary"]
    assert len(page["variants"]["items"]) == 10
    assert sum(b["count"] for b in page["vaf_histogram"]) == body["summary"]["observations"]
