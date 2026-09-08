"""Atomic, idempotent research snapshot loader."""
import os
import uuid
from datetime import UTC, datetime

from psycopg.types.json import Jsonb

from app.db import connection
from app.ingestion.associations import LIMITATIONS, ROOT, replay

DATASET = "Open Targets · ten-gene research associations"


def load_validated(manifest, data):
    report = data["report"]
    if report["invalid"]:
        raise ValueError("Invalid source rows require review")
    if manifest.get("is_fixture") and os.getenv("VERCEL_ENV") == "production":
        raise ValueError("Synthetic production import rejected")
    sha = manifest["sha256"]
    with connection() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(71042028)")
        prior = conn.execute("""SELECT d.id FROM dataset_versions d JOIN ingestion_runs r ON r.dataset_id=d.id
                               WHERE d.name=%s AND d.sha256=%s AND r.status='succeeded'""", (DATASET, sha)).fetchone()
        if prior:
            return {"status": "already_loaded", "dataset_id": prior["id"]}
        sid = conn.execute("""INSERT INTO sources(name,url,license,access_notes) VALUES (%s,%s,%s,%s)
                            ON CONFLICT(name) DO UPDATE SET name=excluded.name RETURNING id""",
                           ("Open Targets", "https://platform.opentargets.org/", manifest["license"],
                            "Includes source-mapped drug mechanisms and Reactome pathways.")).fetchone()["id"]
        metadata = {**manifest, "kind": "research_associations", "pipeline_version": "research-v1",
                    "limitations": LIMITATIONS, "snapshot_git_revision": os.getenv("VERCEL_GIT_COMMIT_SHA")}
        did = conn.execute("""INSERT INTO dataset_versions
                          (source_id,name,version,retrieved_at,sha256,is_fixture,manifest)
                          VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                           (sid, DATASET, sha, manifest["retrieved_at"], sha,
                            manifest.get("is_fixture", False), Jsonb(metadata))).fetchone()["id"]
        for g in data["genes"]:
            conn.execute("""INSERT INTO genes(id,gene_symbol,gene_name) VALUES (%s,%s,%s)
                          ON CONFLICT(id) DO NOTHING""", (g["id"], g["symbol"], g["name"]))
            conn.execute("INSERT INTO research_genes VALUES (%s,%s,%s,%s,%s)",
                         (did, g["id"], g["ensembl"], g["symbol"], g["name"]))
        for d in data["drugs"]:
            conn.execute("""INSERT INTO drugs(id,name,drug_class,dataset_id) VALUES (%s,%s,%s,%s)
                          ON CONFLICT(id) DO NOTHING""", (d["id"], d["name"], d["drug_class"], did))
            conn.execute("INSERT INTO dataset_drugs VALUES (%s,%s,%s,%s,%s)",
                         (did, d["id"], d["name"], d["drug_class"], d["maximum_stage"]))
        for pid, name in data["pathways"].items():
            conn.execute("INSERT INTO pathways VALUES (%s,%s,%s) ON CONFLICT(id) DO NOTHING", (pid, name, did))
            conn.execute("INSERT INTO dataset_pathways VALUES (%s,%s,%s)", (did, pid, name))
        for gid, pid in data["memberships"]:
            conn.execute("INSERT INTO dataset_gene_pathways VALUES (%s,%s,%s)", (did, gid, pid))
            conn.execute("INSERT INTO gene_pathways VALUES (%s,%s) ON CONFLICT DO NOTHING", (gid, pid))
        for a in data["associations"]:
            key = (did, a["gene_id"], a["drug_id"])
            conn.execute("INSERT INTO research_associations VALUES (%s,%s,%s,%s,%s)",
                         (*key, a["maximum_stage"], Jsonb(a["mechanisms"])))
            conn.execute("INSERT INTO drug_targets VALUES (%s,%s,%s,%s,%s)",
                         (a["drug_id"], a["gene_id"], did, "source-mapped mechanism",
                          "https://platform.opentargets.org/drug/" + a["drug_id"]))
            for d in a["diseases"]:
                conn.execute("INSERT INTO research_diseases VALUES (%s,%s,%s,%s,%s)", (*key, d["id"], d["name"]))
            for r in a["reports"]:
                conn.execute("INSERT INTO research_reports VALUES (%s,%s,%s,%s,%s,%s)",
                             (*key, r["id"], r["source"], r["url"]))
        quality = {**report, "method": "Source identifier validation, target-mapped mechanisms and deduplication",
                   "snapshot_sha256": sha, "limitations": LIMITATIONS,
                   "exclusion_reasons": {"unmapped_drug_or_target_mechanism": report["excluded"]},
                   "validation_reasons": {}, "pipeline_version": "research-v1"}
        conn.execute("""INSERT INTO ingestion_runs(id,dataset_id,finished_at,status,
                       downloaded,valid,invalid,excluded,duplicates,report)
                       VALUES (%s,%s,%s,'succeeded',%s,%s,%s,%s,%s,%s)""",
                     (uuid.uuid4(), did, datetime.now(UTC), report["downloaded"], report["valid"],
                      report["invalid"], report["excluded"], report["duplicates"], Jsonb(quality)))
    return {"status": "loaded", "dataset_id": did, "report": report}


def load_snapshot(root=ROOT):
    return load_validated(*replay(root))
