import random

import pytest
from Bio.Align import PairwiseAligner, substitution_matrices
from fastapi.testclient import TestClient

from app.main import app
from app.sequences import align, normalize_sequence, statistics

client = TestClient(app)


@pytest.mark.parametrize("raw,expected", [(" a c\ngtN ", "ACGTN"), (">example\nacgt\nn", "ACGTN")])
def test_normalization(raw, expected):
    assert normalize_sequence(raw, 20) == expected


@pytest.mark.parametrize("raw", ["", " \n", ">header", ">first\nAC\n>second\nGT", "ACGU", "A-C", "ACR", "123"])
def test_rejects_invalid_sequence(raw):
    with pytest.raises(ValueError):
        normalize_sequence(raw, 100)


def test_sequence_limits():
    assert len(normalize_sequence("A" * 1000, 1000)) == 1000
    with pytest.raises(ValueError, match="limit"):
        normalize_sequence("A" * 1001, 1000)


def test_statistics_denominators_and_overlapping_kmers():
    result = statistics("AACGTN", 2)
    assert result["known_bases"] == 5
    assert result["gc_percent"] == 40
    assert result["at_percent"] == 60
    assert result["kmers"]["total_windows"] == 5
    assert result["kmers"]["valid_windows"] == 4
    assert result["kmers"]["excluded_windows"] == 1
    assert statistics("AAAA", 2)["kmers"]["items"] == [{"kmer": "AA", "count": 3, "frequency": 1}]
    assert sum(row["count"] for row in result["composition"]) == 6


def test_all_unknown_and_k_longer_than_sequence():
    result = statistics("NNN", 2)
    assert result["gc_percent"] is None and result["at_percent"] is None
    assert result["kmers"]["items"] == []
    assert result["kmers"]["excluded_windows"] == 2
    assert statistics("AC", 3)["kmers"]["total_windows"] == 0


def test_known_global_traceback_and_score():
    result = align("ACGTACGT", "ACGTCGT", "global", 2, -1, -2)
    assert result["score"] == 12
    assert result["aligned_a"].replace("-", "") == "ACGTACGT"
    assert result["aligned_b"].replace("-", "") == "ACGTCGT"
    assert result["matches"] == 7 and result["gap_columns"] == 1
    assert result["range_a"] == [1, 8] and result["range_b"] == [1, 7]


def test_local_coordinates_and_no_positive_match():
    result = align("TTACGTAA", "GGACGTCC", "local", 2, -1, -2)
    assert result["score"] == 8
    assert result["aligned_a"] == result["aligned_b"] == "ACGT"
    assert result["range_a"] == result["range_b"] == [3, 6]
    empty = align("AAAA", "CCCC", "local", 2, -1, -2)
    assert empty["score"] == 0 and empty["aligned_a"] == ""
    assert empty["identity_percent"] is None and empty["range_a"] is None


def test_unknown_bases_are_not_matches_and_ties_are_deterministic():
    result = align("N", "N", "global", 2, -1, -2)
    assert result["score"] == -1 and result["unknown_pairs"] == 1
    assert result["matches"] == 0
    tied = align("A", "AA", "local", 2, -1, -2)
    assert tied["range_b"] == [1, 1]
    assert tied == align("A", "AA", "local", 2, -1, -2)


@pytest.mark.parametrize("mode", ["global", "local"])
@pytest.mark.parametrize("scores", [(2, -1, -2), (3, -8, -1), (1, 0, -3)])
def test_scores_against_biopython_and_traceback_invariants(mode, scores):
    match, mismatch, gap = scores
    matrix = substitution_matrices.Array(alphabet="ACGTN", dims=2)
    for a in "ACGTN":
        for b in "ACGTN":
            matrix[a, b] = match if a == b and a != "N" else mismatch
    reference = PairwiseAligner(mode=mode)
    reference.substitution_matrix = matrix
    reference.gap_score = gap
    rng = random.Random(4904)
    for _ in range(30):
        a = "".join(rng.choices("ACGTN", k=rng.randint(1, 15)))
        b = "".join(rng.choices("ACGTN", k=rng.randint(1, 15)))
        result = align(a, b, mode, match, mismatch, gap)
        assert result["score"] == reference.score(a, b)
        assert result["score"] == result["matches"] * match + (
            result["mismatches"] + result["unknown_pairs"]) * mismatch + result["gap_columns"] * gap
        assert result["columns"] == len(result["aligned_a"]) == len(result["aligned_b"])
        for key, raw in [("a", a), ("b", b)]:
            span = result["range_" + key]
            observed = result["aligned_" + key].replace("-", "")
            assert observed == (raw[span[0] - 1:span[1]] if span else "")
        if mode == "global":
            assert result["aligned_a"].replace("-", "") == a
            assert result["aligned_b"].replace("-", "") == b


def test_large_alignment_uses_no_preview_and_reaches_boundary():
    result = align("A" * 1000, "A" * 1000, "global", 2, -1, -2)
    assert result["score"] == 2000 and result["matches"] == 1000
    assert result["matrix"]["scores"] is None


def test_statistics_api_works_without_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    response = client.post("/api/sequences/statistics", json={"sequence": ">test\nAACGTN", "k": 2})
    assert response.status_code == 200
    assert response.json()["gc_percent"] == 40
    assert len(response.json()["input"]["sha256"]) == 64
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("payload", [
    {"sequence": "ACGU"}, {"sequence": "A", "k": 0}, {"sequence": "A", "k": 7},
    {"sequence": "A", "k": True}, {"sequence": "A", "extra": 1}, {"sequence": "A" * 100001},
])
def test_statistics_api_validation(payload):
    assert client.post("/api/sequences/statistics", json=payload).status_code == 422


@pytest.mark.parametrize("override", [
    {"mode": "invalid"}, {"match": 0}, {"gap": 0}, {"mismatch": 1}, {"gap": -1.5},
    {"sequence_a": "A" * 1001}, {"sequence_b": ">one\nAC\n>two\nGT"},
])
def test_alignment_api_validation(override):
    payload = {"sequence_a": "ACGT", "sequence_b": "ACGT", **override}
    assert client.post("/api/sequences/align", json=payload).status_code == 422


def test_alignment_api_metadata_and_sanitized_error():
    response = client.post("/api/sequences/align", json={"sequence_a": "ACGT", "sequence_b": "ACGT"})
    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 8 and body["parameters"]["mode"] == "global"
    secret_like = "sensitive_sequence_text"
    invalid = client.post("/api/sequences/align", json={"sequence_a": "A", "sequence_b": "A", "match": secret_like})
    assert invalid.status_code == 422
    assert secret_like not in invalid.text
