import os

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.db import connection
from app.main import app
from scripts.migrate import migrate

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="PostgreSQL required")


@pytest.fixture(scope="module", autouse=True)
def schema():
    if os.getenv("DATABASE_URL"):
        migrate()


def test_migration_is_idempotent():
    migrate()
    with connection() as conn:
        assert conn.execute("SELECT count(*) AS n FROM schema_migrations").fetchone()["n"] == 3


def test_readiness_and_empty_counts():
    client = TestClient(app)
    assert client.get("/api/ready").status_code == 200
    assert client.get("/api/system").json()["counts"] == dict.fromkeys(
        ["samples", "variants", "genes", "drugs", "pathways"], 0)
    assert client.get("/api/genes/MISSING").status_code == 404
    assert client.get("/api/genes").json()["items"] == []


@pytest.mark.parametrize("chromosome,position,ref,alt", [
    ("chr99", 1, "A", "T"), ("1", 0, "A", "T"),
    ("1", 2, "U", "T"), ("1", 2, "A", "A"),
])
def test_invalid_variant_rejected(chromosome, position, ref, alt):
    with pytest.raises(psycopg.errors.CheckViolation), connection() as conn:
        conn.execute("""
            INSERT INTO variants(assembly,chromosome,position,reference_allele,alternate_allele,variant_type)
            VALUES ('GRCh38',%s,%s,%s,%s,'SNV')
        """, (chromosome, position, ref, alt))


def test_variant_deduplication():
    with pytest.raises(psycopg.errors.UniqueViolation), connection() as conn:
        query = """INSERT INTO variants(assembly,chromosome,position,
            reference_allele,alternate_allele,variant_type)
            VALUES ('GRCh38','1',123,'A','T','SNV')"""
        conn.execute(query)
        conn.execute(query)


def test_orphan_gene_relationship_rejected():
    with pytest.raises(psycopg.errors.ForeignKeyViolation), connection() as conn:
        conn.execute("INSERT INTO variant_genes(variant_id,gene_id) VALUES (99999999,99999999)")


def test_sql_input_is_literal():
    client = TestClient(app)
    response = client.get("/api/genes", params={"q": "'; DROP TABLE genes; --"})
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert client.get("/api/genes").status_code == 200
