"""Database connection helpers.

Phase 1: DuckDB (embedded analytics).
Phase 2: add Postgres engine and a config-based switch.

Learning goals:
- Understand context managers for DB connections.
- Learn how to extend this to multiple backends.
"""

from contextlib import contextmanager

import duckdb  # type: ignore

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

# TODO (you, later):
# from sqlalchemy import create_engine
#
# def get_postgres_engine():
#     cfg = get_config()
#     if not cfg.postgres_url:
#         raise RuntimeError("POSTGRES_URL not set")
#     return create_engine(cfg.postgres_url)
#
# def get_engine():
#     """Return DuckDB or Postgres based on config."""
#     cfg = get_config()
#     if cfg.postgres_url:
#         return get_postgres_engine()
#     return get_duckdb_connection()
