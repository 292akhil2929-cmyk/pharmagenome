import logging
import os
import time
import uuid
from datetime import datetime, timezone

import psycopg
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db import connection

logger = logging.getLogger("pharmagenome")
logging.basicConfig(level=logging.INFO)
app = FastAPI(title="PharmaGenome", version="0.1.0",
              description="Research analytics foundation. No medical advice.")
origins = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins,
                   allow_methods=["GET"], allow_headers=["Content-Type"])

TABLES = ["samples", "variants", "genes", "drugs", "pathways"]
EXPECTED_MIGRATION = "001_foundation"


@app.middleware("http")
async def request_metadata(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.monotonic()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    logger.info("request=%s method=%s path=%s status=%d duration_ms=%.1f",
                request_id, request.method, request.url.path, response.status_code,
                (time.monotonic() - start) * 1000)
    return response


@app.exception_handler(psycopg.Error)
async def database_error(request: Request, exc: psycopg.Error):
    logger.error("Database request failed: %s", type(exc).__name__)
    return JSONResponse(status_code=503, content={"detail": "Database temporarily unavailable."})


@app.exception_handler(RuntimeError)
async def configuration_error(request: Request, exc: RuntimeError):
    return JSONResponse(status_code=503, content={"detail": "Database is not configured."})


class Health(BaseModel):
    status: str
    service: str
    version: str


@app.get("/api/health", response_model=Health)
def health():
    return Health(status="ok", service="pharmagenome", version=app.version)


def database_state():
    if not os.getenv("DATABASE_URL"):
        return {"status": "not_configured", "schema_version": None}
    try:
        with connection() as conn:
            row = conn.execute("SELECT version FROM schema_migrations WHERE version = %s",
                               (EXPECTED_MIGRATION,)).fetchone()
            return {"status": "ready" if row else "migration_required",
                    "schema_version": row["version"] if row else None}
    except psycopg.errors.UndefinedTable:
        return {"status": "migration_required", "schema_version": None}
    except psycopg.Error:
        return {"status": "unavailable", "schema_version": None}


@app.get("/api/ready")
def ready():
    state = database_state()
    return JSONResponse(status_code=200 if state["status"] == "ready" else 503,
                        content=state)


@app.get("/api/system")
def system():
    state = database_state()
    counts = None
    datasets = []
    if state["status"] == "ready":
        with connection() as conn:
            counts = {table: conn.execute(
                psycopg.sql.SQL("SELECT count(*) AS count FROM {}").format(
                    psycopg.sql.Identifier(table))).fetchone()["count"] for table in TABLES}
            datasets = conn.execute("""
                SELECT d.id, d.name, d.version, d.retrieved_at, d.is_fixture,
                       s.name AS source, s.url, s.license,
                       r.status AS ingestion_status, r.valid, r.invalid, r.duplicates
                FROM dataset_versions d JOIN sources s ON s.id=d.source_id
                LEFT JOIN LATERAL (
                    SELECT * FROM ingestion_runs WHERE dataset_id=d.id
                    ORDER BY started_at DESC LIMIT 1
                ) r ON true ORDER BY d.retrieved_at DESC LIMIT 100
            """).fetchall()
    return {"service": "PharmaGenome", "version": app.version, "phase": 1,
            "checked_at": datetime.now(timezone.utc), "database": state,
            "counts": counts, "datasets": datasets,
            "limitations": ["No analytical modules are released in Phase 1.",
                            "No datasets are seeded automatically.",
                            "Research and education only; not medical advice."]}


@app.get("/api/genes")
def genes(q: str = Query("", max_length=80),
          page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100)):
    with connection() as conn:
        pattern = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        total = conn.execute("SELECT count(*) AS n FROM genes WHERE gene_symbol ILIKE %s",
                             (pattern,)).fetchone()["n"]
        rows = conn.execute("""
            SELECT id,gene_symbol,gene_name,description FROM genes
            WHERE gene_symbol ILIKE %s ORDER BY gene_symbol LIMIT %s OFFSET %s
        """, (pattern, page_size, (page - 1) * page_size)).fetchall()
    return {"items": rows, "total": total, "page": page, "page_size": page_size}


@app.get("/api/genes/{symbol}")
def gene(symbol: str):
    if len(symbol) > 80:
        raise HTTPException(422, "Gene symbol must be at most 80 characters.")
    with connection() as conn:
        row = conn.execute("SELECT * FROM genes WHERE gene_symbol=%s", (symbol.upper(),)).fetchone()
    if not row:
        raise HTTPException(404, "Gene not found in the imported datasets.")
    return row
