import copy
import os
import uuid
from contextlib import contextmanager
from pathlib import Path

import psycopg
import pytest

from app.db import connection
from app.ingestion import load
from app.ingestion.normalize import normalize
from tests.fixtures_ingestion import fixture_manifest, fixture_payload

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="PostgreSQL required")


@pytest.fixture
def isolated_database(monkeypatch):
    # Schema and every test record disappear on rollback; no shared-table truncation.
    with connection() as conn:
        schema = "test_ingestion_" + uuid.uuid4().hex
        conn.execute(psycopg.sql.SQL("CREATE SCHEMA {}").format(psycopg.sql.Identifier(schema)))
        conn.execute(psycopg.sql.SQL("SET LOCAL search_path TO {}").format(psycopg.sql.Identifier(schema)))
        root = Path(__file__).resolve().parents[1]
        for path in sorted((root / "migrations").glob("*.sql")):
            conn.execute(path.read_text(encoding="utf-8"))

        @contextmanager
        def scoped_connection():
            with conn.transaction():
                yield conn

        monkeypatch.setattr(load, "connection", scoped_connection)
        yield conn
        conn.rollback()


def test_import_is_idempotent_and_includes_zero_observation_sample(isolated_database):
    manifest, data = fixture_manifest(), normalize(fixture_payload())
    first = load.load_validated(manifest, data)
    second = load.load_validated(manifest, data)
    assert first["status"] == "loaded"
    assert second == {"status": "already_loaded", "dataset_id": first["dataset_id"]}
    conn = isolated_database
    assert conn.execute("SELECT count(*) AS n FROM samples").fetchone()["n"] == 2
    assert conn.execute("SELECT count(*) AS n FROM sample_variants").fetchone()["n"] == 1
    assert conn.execute("SELECT is_fixture FROM dataset_versions").fetchone()["is_fixture"] is True


def test_snapshot_versions_preserve_older_observations(isolated_database):
    manifest, data = fixture_manifest(), normalize(fixture_payload())
    load.load_validated(manifest, data)
    later = copy.deepcopy(data)
    later["observations"][0]["vaf"] = 0.5
    load.load_validated({**manifest, "sha256": "b" * 64}, later)
    rows = isolated_database.execute(
        "SELECT variant_allele_fraction FROM sample_variants ORDER BY variant_allele_fraction"
    ).fetchall()
    assert [r["variant_allele_fraction"] for r in rows] == [0.25, 0.5]


def test_database_constraint_rolls_back_entire_import(isolated_database):
    data = normalize(fixture_payload())
    data["observations"][0]["ref"] = "U"
    with pytest.raises(psycopg.errors.CheckViolation):
        load.load_validated(fixture_manifest(), data)
    for table in ["dataset_versions", "samples", "genes", "ingestion_runs"]:
        n = isolated_database.execute(
            psycopg.sql.SQL("SELECT count(*) AS n FROM {}").format(psycopg.sql.Identifier(table))
        ).fetchone()["n"]
        assert n == 0


def test_production_rejects_fixture(monkeypatch, isolated_database):
    monkeypatch.setenv("VERCEL_ENV", "production")
    with pytest.raises(ValueError, match="fixtures"):
        load.load_validated(fixture_manifest(), normalize(fixture_payload()))
