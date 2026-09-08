"""Apply immutable, checksummed migrations under a PostgreSQL advisory lock."""
import hashlib
from pathlib import Path

from app.db import connection

ROOT = Path(__file__).resolve().parents[1]


def migrate():
    with connection() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(71042026)")
        conn.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
            version text PRIMARY KEY, checksum text NOT NULL,
            applied_at timestamptz NOT NULL DEFAULT now())""")
        for path in sorted((ROOT / "migrations").glob("*.sql")):
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode()).hexdigest()
            existing = conn.execute("SELECT checksum FROM schema_migrations WHERE version=%s",
                                    (path.stem,)).fetchone()
            if existing:
                if existing["checksum"] != checksum:
                    raise RuntimeError(f"Applied migration was modified: {path.stem}")
                continue
            conn.execute(sql)
            conn.execute("INSERT INTO schema_migrations(version,checksum) VALUES (%s,%s)",
                         (path.stem, checksum))
            print(f"Applied {path.stem}")


if __name__ == "__main__":
    migrate()
