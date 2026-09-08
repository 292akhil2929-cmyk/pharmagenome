import copy
import json
import shutil

import pytest

from app.ingestion.normalize import normalize
from app.ingestion.snapshot import SNAPSHOT, read_snapshot
from tests.fixtures_ingestion import fixture_payload


def test_normalization_keeps_unmutated_samples():
    data = normalize(fixture_payload())
    assert len(data["samples"]) == 2
    assert len(data["observations"]) == 1
    assert data["observations"][0]["vaf"] == 0.25
    assert data["report"]["downloaded"] == 1


@pytest.mark.parametrize("field,value", [
    ("chr", "99"), ("startPosition", 1001), ("referenceAllele", "U"),
    ("ncbiBuild", "GRCh38"), ("sampleId", "UNKNOWN"), ("entrezGeneId", 123),
    ("molecularProfileId", "wrong"), ("variantAllele", "A"),
    ("startPosition", True), ("tumorAltCount", -2), ("tumorRefCount", 1.5),
])
def test_bad_observation_is_quarantined(field, value):
    payload = fixture_payload()
    payload["mutations-7157.json"][0][field] = value
    report = normalize(payload)["report"]
    assert report["invalid"] == 1
    assert report["valid"] == 0
    assert report["downloaded"] == report["invalid"]


def test_exclusions_are_separate_from_invalid():
    payload = fixture_payload()
    payload["mutations-7157.json"][0].update(variantType="DEL", referenceAllele="AA", variantAllele="-")
    report = normalize(payload)["report"]
    assert (report["valid"], report["invalid"], report["excluded"]) == (0, 0, 1)
    assert report["exclusion_reasons"] == {"non_SNV": 1}


def test_duplicate_observation_is_counted_once():
    payload = fixture_payload()
    payload["mutations-7157.json"] *= 2
    report = normalize(payload)["report"]
    assert (report["downloaded"], report["valid"], report["duplicates"]) == (2, 1, 1)


def test_conflicting_duplicate_aborts():
    payload = fixture_payload()
    duplicate = copy.deepcopy(payload["mutations-7157.json"][0])
    duplicate["tumorAltCount"] = 9
    payload["mutations-7157.json"].append(duplicate)
    with pytest.raises(RuntimeError, match="Conflicting duplicate"):
        normalize(payload)


@pytest.mark.parametrize("counts", [(None, None), (-1, -1), (0, 0)])
def test_unknown_vaf_is_null(counts):
    payload = fixture_payload()
    payload["mutations-7157.json"][0].update(tumorAltCount=counts[0], tumorRefCount=counts[1])
    data = normalize(payload)
    assert data["observations"][0]["vaf"] is None
    assert data["report"]["missing_vaf"] == 1


def test_incomplete_cohort_fails_closed():
    payload = fixture_payload()
    payload["sample_ids.json"] = ["TEST-A"]
    with pytest.raises(ValueError, match="cohort"):
        normalize(payload)


def test_empty_cohort_fails_closed():
    payload = fixture_payload()
    payload["sample_ids.json"] = []
    with pytest.raises(ValueError, match="cohort"):
        normalize(payload)


def test_pinned_public_snapshot():
    manifest, payload = read_snapshot()
    report = normalize(payload)["report"]
    assert manifest["sha256"] == "aae580bb94295d59dfa7e18676fd7ce62547881958bd0919169f0b1bcc1ca78f"
    assert manifest["is_fixture"] is False
    assert (report["samples"], report["genes"]) == (566, 10)
    assert (report["downloaded"], report["valid"], report["excluded"], report["invalid"]) == (966, 839, 127, 0)
    assert report["unique_variants"] == 506


def test_raw_tampering_is_rejected(tmp_path):
    shutil.copytree(SNAPSHOT, tmp_path / "snapshot")
    (tmp_path / "snapshot" / "raw" / "gene-7157.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Raw checksum mismatch"):
        read_snapshot(tmp_path / "snapshot")


def test_manifest_path_injection_is_rejected(tmp_path):
    manifest = json.loads((SNAPSHOT / "manifest.json").read_text(encoding="utf-8"))
    manifest["files"]["../../secret"] = {"sha256": "a" * 64}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="scope/schema"):
        read_snapshot(tmp_path)
