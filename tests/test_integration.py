import pytest
import os
import duckdb
from app.config import get_config

def test_config_loading():
    cfg = get_config()
    assert "AAPL" in cfg.symbols_list

def test_db_init():
    from app.db.utils import init_user_tables
    init_user_tables()
    cfg = get_config()
    with duckdb.connect(str(cfg.duckdb_path)) as conn:
        tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]
        assert "watchlist" in tables
        assert "holdings" in tables

def test_airflow_dag():
    from airflow.models import DagBag
    dagbag = DagBag(dag_folder="airflow/dags", include_examples=False)
    assert "market_data_etl" in dagbag.dags
