"""Atomic, idempotent CellMiner modeling snapshot loader."""
import os
import uuid
from datetime import UTC, datetime

from psycopg.types.json import Jsonb

from app.db import connection
from app.ingestion.modeling import GENES, LIMITATIONS, ROOT, replay

DATASET = "CellMiner NCI-60 · ten-gene / ten-drug modeling panel"
GENE_IDS = {"BRAF": 673, "EGFR": 1956, "KRAS": 3845, "MET": 4233, "NF1": 4763,
            "PIK3CA": 5290, "RB1": 5925, "STK11": 6794, "TP53": 7157, "KEAP1": 9817}


def load_validated(manifest, data):
    report = data["report"]
    if report["invalid"]:
        raise ValueError("Invalid CellMiner rows require review")
    if manifest.get("is_fixture") and os.getenv("VERCEL_ENV") == "production":
        raise ValueError("Synthetic production import rejected")
    with connection() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(71042029)")
        prior = conn.execute("""SELECT d.id FROM dataset_versions d JOIN ingestion_runs r ON r.dataset_id=d.id
            WHERE d.name=%s AND d.sha256=%s AND r.status='succeeded'""",
                             (DATASET, manifest["sha256"])).fetchone()
        if prior:
            return {"status": "already_loaded", "dataset_id": prior["id"]}
        source_id = conn.execute("""INSERT INTO sources(name,url,license,access_notes) VALUES (%s,%s,%s,%s)
            ON CONFLICT(name) DO UPDATE SET name=excluded.name RETURNING id""",
            ("NCI CellMiner", manifest["source_url"], "NCI reuse policy; credit National Cancer Institute",
             "Processed CellMiner 2025.3 values. Upstream ZIP checksums are preserved in the manifest.")).fetchone()["id"]
        metadata = {**manifest, "kind": "drug_response_modeling", "pipeline_version": "cellminer-model-v1",
                    "limitations": LIMITATIONS, "snapshot_git_revision": os.getenv("VERCEL_GIT_COMMIT_SHA")}
        dataset_id = conn.execute("""INSERT INTO dataset_versions
            (source_id,name,version,retrieved_at,sha256,is_fixture,manifest)
            VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (source_id, DATASET, manifest["version"], manifest["retrieved_at"], manifest["sha256"],
             manifest.get("is_fixture", False), Jsonb(metadata))).fetchone()["id"]
        disease_id = conn.execute("""INSERT INTO diseases(name,ontology_id,description) VALUES (%s,%s,%s)
            ON CONFLICT(ontology_id) DO UPDATE SET name=excluded.name RETURNING id""",
            ("NCI-60 cancer cell-line panel", "cellminer:nci60",
             "Mixed-tissue experimental cell-line panel; not individual diagnoses.")).fetchone()["id"]
        study_id = "cellminer-nci60"
        conn.execute("INSERT INTO studies(id,name,dataset_id) VALUES (%s,%s,%s) ON CONFLICT(id) DO NOTHING",
                     (study_id, "NCI-60 CellMiner", dataset_id))
        conn.execute("INSERT INTO study_dataset_versions(study_id,dataset_id) VALUES (%s,%s)", (study_id, dataset_id))
        for gene in GENES:
            gid = GENE_IDS[gene]
            conn.execute("""INSERT INTO genes(id,gene_symbol,gene_name) VALUES (%s,%s,%s)
                ON CONFLICT(id) DO NOTHING""", (gid, gene, gene))
            conn.execute("INSERT INTO dataset_genes VALUES (%s,%s,%s,%s)",
                         (dataset_id, gid, gene, "CellMiner expression and mutation feature"))
        for drug in manifest["drugs"]:
            drug_id = "NSC:" + drug["nsc"]
            conn.execute("""INSERT INTO drugs(id,name,drug_class,mechanism,approval_status,dataset_id)
                VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING""",
                (drug_id, drug["name"], "CellMiner FDA-approved panel", drug["mechanism"],
                 drug["fda_status"], dataset_id))
            conn.execute("INSERT INTO dataset_drugs VALUES (%s,%s,%s,%s,%s)",
                         (dataset_id, drug_id, drug["name"], drug["mechanism"], drug["fda_status"]))
        for record in data["records"]:
            sample_id = conn.execute("""INSERT INTO samples
                (sample_identifier,disease_id,study_id,tissue) VALUES (%s,%s,%s,%s)
                ON CONFLICT(study_id,sample_identifier) DO UPDATE SET tissue=excluded.tissue RETURNING id""",
                (record["cell_line"], disease_id, study_id, record["tissue"])).fetchone()["id"]
            for gene, values in record["features"].items():
                for kind, unit in (("expression", "z score"), ("mutation", "binary present/absent")):
                    value = values[kind]
                    if value is not None:
                        conn.execute("INSERT INTO cell_line_features VALUES (%s,%s,%s,%s,%s,%s)",
                            (dataset_id, sample_id, GENE_IDS[gene],
                             "expression_z_score" if kind == "expression" else "protein_affecting_mutation",
                             value, unit))
            for nsc, value in record["responses"].items():
                if value is not None:
                    conn.execute("""INSERT INTO drug_responses
                        (sample_id,drug_id,dataset_id,replicate,response_value,measurement_type,unit)
                        VALUES (%s,%s,%s,'CellMiner average',%s,'compound activity average z score','z score')""",
                        (sample_id, "NSC:" + nsc, dataset_id, value))
        quality = {**report, "snapshot_sha256": manifest["sha256"], "pipeline_version": "cellminer-model-v1",
                   "method": "Checksum, schema, identifier, range and missing-value validation",
                   "parameters": {"genes": GENES, "drugs": [d["nsc"] for d in manifest["drugs"]]},
                   "limitations": LIMITATIONS, "validation_reasons": {}, "exclusion_reasons": {}}
        conn.execute("""INSERT INTO ingestion_runs(id,dataset_id,finished_at,status,
            downloaded,valid,invalid,excluded,duplicates,report)
            VALUES (%s,%s,%s,'succeeded',%s,%s,%s,%s,%s,%s)""",
            (uuid.uuid4(), dataset_id, datetime.now(UTC), report["downloaded"], report["valid"],
             report["invalid"], report["excluded"], report["duplicates"], Jsonb(quality)))
    return {"status": "loaded", "dataset_id": dataset_id, "report": report}


def load_snapshot(root=ROOT):
    return load_validated(*replay(root))
