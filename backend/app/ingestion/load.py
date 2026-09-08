"""Atomic loading with a snapshot-specific profile and an idempotency lock."""
import json
import os
import uuid
from datetime import UTC, datetime

from psycopg.types.json import Jsonb

from app.db import connection
from app.ingestion.normalize import normalize
from app.ingestion.snapshot import LIMITATIONS, SNAPSHOT, read_snapshot

DATASET_NAME = "TCGA LUAD · ten-gene SNV subset"


def load_validated(manifest, data):
    report = data["report"]
    if report["invalid"]:
        raise ValueError("Invalid source records require review; no database rows were changed")
    if manifest.get("is_fixture") and os.getenv("VERCEL_ENV") == "production":
        raise ValueError("Development fixtures cannot be loaded into production")
    sha = manifest["sha256"]
    # Snapshot identity namespaces the observation profile, preserving earlier versions.
    internal_profile = manifest["profile_id"] + "@" + sha
    started = datetime.now(UTC)
    with connection() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(71042027)")
        prior = conn.execute("""
            SELECT d.id FROM dataset_versions d JOIN ingestion_runs r ON r.dataset_id=d.id
            WHERE d.sha256=%s AND d.name=%s AND r.status='succeeded'
        """, (sha, DATASET_NAME)).fetchone()
        if prior:
            return {"status": "already_loaded", "dataset_id": prior["id"]}
        source_id = conn.execute("""
            INSERT INTO sources(name,url,license,access_notes) VALUES (%s,%s,%s,%s)
            ON CONFLICT(name) DO UPDATE SET name=excluded.name RETURNING id
        """, ("cBioPortal / TCGA", "https://www.cbioportal.org/study/summary?id=" + manifest["study_id"],
              manifest["license"], "Public study. Cite cBioPortal and TCGA; derived data retain source terms.")).fetchone()["id"]
        provenance = {**manifest, "limitations": LIMITATIONS, "assembly": "GRCh37",
                      "pipeline_version": "luad-snv-v1", "snapshot_git_revision": os.getenv("VERCEL_GIT_COMMIT_SHA")}
        dataset_id = conn.execute("""
            INSERT INTO dataset_versions(source_id,name,version,retrieved_at,sha256,is_fixture,manifest)
            VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (source_id, DATASET_NAME, sha, manifest["retrieved_at"], sha,
              manifest.get("is_fixture", False), Jsonb(provenance))).fetchone()["id"]
        disease_id = conn.execute("""
            INSERT INTO diseases(name,ontology_id,description) VALUES (%s,%s,%s)
            ON CONFLICT(ontology_id) DO UPDATE SET name=excluded.name RETURNING id
        """, (data["study"]["cancerType"]["name"], "cbioportal:" + data["study"]["cancerTypeId"],
              "Disease category supplied by cBioPortal; not an individual diagnosis.")).fetchone()["id"]
        study_id = data["study"]["studyId"]
        conn.execute("""
            INSERT INTO studies(id,name,dataset_id) VALUES (%s,%s,%s) ON CONFLICT(id) DO NOTHING
        """, (study_id, data["study"]["name"], dataset_id))
        conn.execute("INSERT INTO study_dataset_versions(study_id,dataset_id) VALUES (%s,%s)",
                     (study_id, dataset_id))
        conn.execute("""
            INSERT INTO molecular_profiles(id,study_id,assay_type,dataset_id) VALUES (%s,%s,%s,%s)
        """, (internal_profile, study_id, "WES mutation profile; ten-gene SNV import", dataset_id))
        for gene in data["genes"]:
            conn.execute("""
                INSERT INTO genes(id,gene_symbol,gene_name,description) VALUES (%s,%s,NULL,%s)
                ON CONFLICT(id) DO NOTHING
            """, (gene["id"], gene["symbol"], "Symbol/type from cBioPortal. Full gene name not supplied."))
            conn.execute("""
                INSERT INTO dataset_genes(dataset_id,gene_id,source_symbol,source_type) VALUES (%s,%s,%s,%s)
            """, (dataset_id, gene["id"], gene["symbol"], gene["type"]))
            conn.execute("INSERT INTO profile_genes(profile_id,gene_id) VALUES (%s,%s)",
                         (internal_profile, gene["id"]))
        sample_ids = {}
        for sample in data["samples"]:
            row = conn.execute("""
                INSERT INTO samples(sample_identifier,patient_identifier,disease_id,study_id,tissue)
                VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT(study_id,sample_identifier) DO UPDATE
                SET sample_identifier=excluded.sample_identifier RETURNING id
            """, (sample["sampleId"], sample.get("patientId"), disease_id, study_id,
                  None)).fetchone()
            sample_ids[sample["sampleId"]] = row["id"]
            conn.execute("INSERT INTO profile_samples(profile_id,sample_id) VALUES (%s,%s)",
                         (internal_profile, row["id"]))
        variant_ids = {}
        for row in data["observations"]:
            key = (row["chromosome"], row["position"], row["ref"], row["alt"])
            if key not in variant_ids:
                variant_ids[key] = conn.execute("""
                    INSERT INTO variants(assembly,chromosome,position,reference_allele,alternate_allele,variant_type)
                    VALUES ('GRCh37',%s,%s,%s,%s,'SNV')
                    ON CONFLICT(assembly,chromosome,position,reference_allele,alternate_allele)
                    DO UPDATE SET position=excluded.position RETURNING id
                """, key).fetchone()["id"]
            variant_id = variant_ids[key]
            for gene_id, consequence in row["genes"].items():
                conn.execute("""
                    INSERT INTO variant_genes(variant_id,gene_id,consequence) VALUES (%s,%s,%s)
                    ON CONFLICT(variant_id,gene_id) DO NOTHING
                """, (variant_id, int(gene_id), consequence))
                conn.execute("""
                    INSERT INTO dataset_variant_genes(dataset_id,variant_id,gene_id,consequence)
                    VALUES (%s,%s,%s,%s) ON CONFLICT(dataset_id,variant_id,gene_id) DO NOTHING
                """, (dataset_id, variant_id, int(gene_id), consequence))
            conn.execute("""
                INSERT INTO sample_variants(sample_id,variant_id,profile_id,dataset_id,variant_allele_fraction)
                VALUES (%s,%s,%s,%s,%s)
            """, (sample_ids[row["sample"]], variant_id, internal_profile, dataset_id, row["vaf"]))
        report_id = uuid.uuid4()
        report = {**report, "snapshot_sha256": sha, "pipeline_version": "luad-snv-v1",
                  "parameters": {"gene_ids": manifest["selected_gene_ids"], "assembly": "GRCh37", "variant_type": "SNV"},
                  "limitations": LIMITATIONS}
        conn.execute("""
            INSERT INTO ingestion_runs(id,dataset_id,started_at,finished_at,status,
                                       downloaded,valid,invalid,excluded,duplicates,report)
            VALUES (%s,%s,%s,%s,'succeeded',%s,%s,%s,%s,%s,%s)
        """, (report_id, dataset_id, started, datetime.now(UTC), report["downloaded"],
              report["valid"], report["invalid"], report["excluded"], report["duplicates"], Jsonb(report)))
    return {"status": "loaded", "dataset_id": dataset_id,
            "report": {k: v for k, v in report.items() if k != "rejected_records"}}


def load_snapshot(root=SNAPSHOT):
    manifest, payload = read_snapshot(root)
    return load_validated(manifest, normalize(payload))


if __name__ == "__main__":
    print(json.dumps(load_snapshot(), indent=2))
