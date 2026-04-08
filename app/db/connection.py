"""Database connection helpers.

Phase 1: DuckDB (embedded analytics).
Phase 2: add Postgres engine and a config-based switch.

Learning goals:
- Understand context managers for DB connections.
- Learn how to extend this to multiple backends.
"""

from contextlib import contextmanager

import duckdb  # type: ignore
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.engine import Engine

from app.config import get_config


@contextmanager
def get_duckdb_connection():
    cfg = get_config()
    db_path = cfg.duckdb_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))
    try:
        yield conn
    finally:
        conn.close()


def get_postgres_engine() -> Engine:
    cfg = get_config()
    if not cfg.postgres_url:
        raise RuntimeError("POSTGRES_URL must be set to use Postgres")
    return create_engine(cfg.postgres_url)


def get_db_engine():
    cfg = get_config()
    if cfg.postgres_url:
        return get_postgres_engine()
    return None


@contextmanager
def get_connection():
    cfg = get_config()
    if cfg.postgres_url:
        engine = get_postgres_engine()
        with engine.begin() as conn:
            yield conn
    else:
        with get_duckdb_connection() as conn:
            yield conn

