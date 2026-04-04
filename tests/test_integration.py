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
        assert "user_stocks" in tables


def test_watchlist_and_holdings_crud():
    from app.db.utils import (
        init_user_tables,
        add_to_watchlist,
        get_watchlist_symbols,
        remove_from_watchlist,
        update_holding,
        get_holdings,
        remove_holding,
    )

    init_user_tables()

    add_to_watchlist("AAPL", tags="tech", note="Core holding")
    assert "AAPL" in get_watchlist_symbols()

    remove_from_watchlist("AAPL")
    assert "AAPL" not in get_watchlist_symbols()

    update_holding("MSFT", 5.0, 280.0)
    holdings = get_holdings()
    assert any(h["symbol"] == "MSFT" for h in holdings)

    remove_holding("MSFT")
    holdings_after = get_holdings()
    assert not any(h["symbol"] == "MSFT" for h in holdings_after)


def test_airflow_dag():
    from airflow.models import DagBag
    dagbag = DagBag(dag_folder="airflow/dags", include_examples=False)
    assert "market_data_etl" in dagbag.dags
