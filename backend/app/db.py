import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


@contextmanager
def connection():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("database_not_configured")
    with psycopg.connect(url, connect_timeout=5, row_factory=dict_row) as conn:
        conn.execute("SET LOCAL statement_timeout = 5000")
        yield conn
