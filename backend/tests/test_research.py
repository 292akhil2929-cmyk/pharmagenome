import copy
import json
import os

import pytest
from fastapi.testclient import TestClient

from app import research
from app.ingestion import load, load_associations
from app.ingestion.associations import GENES, ROOT, normalize, replay, safe_url
from app.main import app
from app.research import compute
from tests.test_ingestion_db import isolated_database  # noqa: F401

client = TestClient(app)


def payload():
    return {p.name: json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "raw").glob("*.json")}


def test_public_snapshot_reconciles_and_maps_mechanisms():
    manifest, data = replay()
    assert manifest["sha256"] == "a203c4635eac2cdb679f4081c1163a730d70f78745b54f17b566ebf5b5c3b3cb"
    assert data["report"]["downloaded"] == 186
    assert data["report"]["valid"] == 186
    assert data["report"]["invalid"] == data["report"]["excluded"] == data["report"]["duplicates"] == 0
    assert len(data["genes"]) == 10
    assert len(data["pathways"]) == 220
    assert len(data["memberships"]) == 279
    gene_map = {g["id"]: g["ensembl"] for g in data["genes"]}
    for a in data["associations"]:
        assert all(gene_map[a["gene_id"]] in m["target_ids"] for m in a["mechanisms"])


def test_rejects_gene_mismatch_and_partial_source_response():
    p = payload()
    p["gene-EGFR.json"]["display_name"] = "WRONG"
    with pytest.raises(ValueError, match="identifier mismatch"):
        normalize(p)
    p = payload()
    p["target-EGFR.json"]["data"]["target"]["drugAndClinicalCandidates"]["count"] += 1
    with pytest.raises(ValueError, match="Truncated"):
        normalize(p)


def test_excludes_unmapped_mechanism_and_deduplicates():
    p = payload()
    rows = p["target-EGFR.json"]["data"]["target"]["drugAndClinicalCandidates"]
    rows["rows"][0]["drug"]["mechanismsOfAction"] = None
    rows["rows"].append(copy.deepcopy(rows["rows"][1]))
    rows["count"] += 1
    data = normalize(p)
    assert data["report"]["excluded"] == 1
    assert data["report"]["duplicates"] == 1
    assert data["report"]["downloaded"] == 187
    assert data["report"]["invalid"] == 0


def test_conflicting_duplicate_is_invalid_and_unsafe_links_rejected():
    p = payload()
    rows = p["target-EGFR.json"]["data"]["target"]["drugAndClinicalCandidates"]
    duplicate = copy.deepcopy(rows["rows"][0])
    duplicate["maxClinicalStage"] = "conflicting"
    rows["rows"].append(duplicate)
    rows["count"] += 1
    assert normalize(p)["report"]["invalid"] == 1
    assert safe_url("http://example.org/source") == "http://example.org/source"
    assert safe_url(None) is None
    with pytest.raises(ValueError):
        safe_url("javascript:alert(1)")


def test_checksum_tampering_rejected(tmp_path):
    import shutil
    shutil.copytree(ROOT, tmp_path / "snapshot")
    (tmp_path / "snapshot/raw/gene-EGFR.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        replay(tmp_path / "snapshot")


def example():
    genes = [{"id": 1, "symbol": "A"}, {"id": 2, "symbol": "B"}, {"id": 3, "symbol": "C"}]
    drugs = [{"id": "D1", "name": "Drug one", "drug_class": "Small", "maximum_stage": "PHASE_1"},
             {"id": "D2", "name": "Drug two", "drug_class": "Other", "maximum_stage": "PHASE_2"}]
    pathways = [{"id": "P1", "name": "Shared", "gene_id": 1}, {"id": "P1", "name": "Shared", "gene_id": 2},
                {"id": "P2", "name": "Single", "gene_id": 1}]
    base = {"maximum_stage": "PHASE_1", "mechanisms": [], "diseases": [{"id": "E1", "name": "Example"}],
            "reports": [{"source": "source", "id": "same-report", "url": None}]}
    links = [{**base, "gene_id": 1, "drug_id": "D1"}, {**base, "gene_id": 2, "drug_id": "D1"},
             {**base, "gene_id": 1, "drug_id": "D2", "diseases": []}]
    return genes, drugs, pathways, links


def test_overlap_denominator_distinct_reports_and_drugs():
    result = compute(*example(), ["A", "B", "C"])
    assert result["summary"] == {"selected_genes": 3, "drugs": 2, "target_links": 3, "pathways": 2}
    assert result["pathways"]["items"][0]["overlap"] == 2
    assert result["pathways"]["items"][0]["selected_gene_count"] == 3
    assert result["drugs"]["items"][0]["report_count"] == 1
    assert len(result["drugs"]["items"][0]["targets"]) == 2


def test_drug_filters_do_not_change_pathway_overlap_and_pages_clamp():
    result = compute(*example(), ["A", "B"], disease="E1", page_size=1, page=99, pathway_page=99)
    assert result["drugs"]["total"] == 1
    assert result["drugs"]["page"] == 1
    assert result["pathways"]["total"] == 2
    assert result["pathways"]["page"] == 2
    assert compute(*example(), ["A"], q="%")["drugs"]["total"] == 0
    assert compute(*example(), ["C"])["pathways"]["items"] == []
    assert compute(*example(), ["A"], drug_class="Other")["drugs"]["items"][0]["id"] == "D2"
    assert compute(*example(), ["A"], stage="PHASE_1")["drugs"]["total"] == 1


@pytest.mark.parametrize("query", ["page=0", "page_size=101", "pathway_page=-1", "dataset_id=0",
                                   "genes=" + "x" * 201, "sort=bad", "q=" + "x" * 81])
def test_api_validation(query):
    assert client.get("/api/research?" + query).status_code == 422


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="PostgreSQL required")
@pytest.mark.usefixtures("isolated_database")
def test_import_snapshot_isolation_api_and_idempotency(monkeypatch):
    monkeypatch.setattr(load_associations, "connection", load.connection)
    monkeypatch.setattr(research, "connection", load.connection)
    manifest, data = replay()
    first = load_associations.load_validated(manifest, data)
    assert load_associations.load_validated(manifest, data)["status"] == "already_loaded"
    older = client.get("/api/research", params={"dataset_id": first["dataset_id"], "genes": "EGFR"})
    assert older.status_code == 200
    body = older.json()
    assert body["summary"]["drugs"] == 82
    assert body["summary"]["pathways"] == 37
    assert body["selected_genes"][0]["id"] == GENES["EGFR"]
    changed = copy.deepcopy(data)
    changed["associations"] = []
    changed["memberships"] = []
    changed["drugs"] = []
    changed["pathways"] = {}
    changed["report"].update(downloaded=0, valid=0)
    second = load_associations.load_validated({**manifest, "sha256": "b" * 64}, changed)
    assert client.get("/api/research", params={"dataset_id": second["dataset_id"]}).json()["summary"]["drugs"] == 0
    assert client.get("/api/research", params={"dataset_id": first["dataset_id"], "genes": "EGFR"}).json()["summary"] == body["summary"]
    assert client.get("/api/research?dataset_id=99999999").status_code == 404
    assert client.get("/api/research?genes=UNIMPORTED").status_code == 422
    assert client.get("/api/research?genes=EGFR,EGFR").json()["summary"]["selected_genes"] == 1


def test_fixture_and_invalid_rows_cannot_enter_production(monkeypatch):
    manifest, data = replay()
    monkeypatch.setenv("VERCEL_ENV", "production")
    with pytest.raises(ValueError, match="Synthetic"):
        load_associations.load_validated({**manifest, "is_fixture": True}, data)
    data["report"]["invalid"] = 1
    with pytest.raises(ValueError, match="Invalid"):
        load_associations.load_validated(manifest, data)
