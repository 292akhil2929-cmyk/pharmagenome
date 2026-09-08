import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


@contextmanager
def connection():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("database_not_configured")
    with psycopg.connect(url, connect_timeout=5, row_factory=dict_row,
                         options="-c statement_timeout=5000") as conn:
        yield conn
