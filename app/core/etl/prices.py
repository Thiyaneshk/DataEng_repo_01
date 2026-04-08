import uuid
from datetime import datetime
from typing import Optional, List
import duckdb
import pandas as pd
import yfinance as yf
from sqlalchemy import text
from app.db.connection import get_duckdb_connection, get_connection
from app.config import get_config

def fetch_prices_5m(symbols: List[str], period: str = "5d") -> pd.DataFrame:
    if not symbols: return pd.DataFrame()
    raw = yf.download(tickers=symbols, period=period, interval="5m", group_by="ticker", auto_adjust=True)
    if raw.empty: return pd.DataFrame()
    frames = []
    for sym in symbols:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                if sym not in raw.columns.levels[0]: continue
                df = raw.xs(sym, axis=1, level=0, drop_level=True).copy()
            else: df = raw.copy()
            df = df.dropna(how="all").reset_index()
            df.columns = [str(c).lower() for c in df.columns]
            time_col = "datetime" if "datetime" in df.columns else "date"
            df = df.rename(columns={time_col: "datetime"})
            df["symbol"] = sym
            frames.append(df[["symbol", "datetime", "open", "high", "low", "close", "volume"]])
        except Exception: continue
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def load_prices_5m(symbols=None, period=None, conn=None) -> int:
    cfg = get_config()
    symbols = symbols or cfg.symbols_list
    period = period or cfg.default_period
    df = fetch_prices_5m(symbols, period)
    if df.empty: return 0
    df["source_load_ts"] = datetime.utcnow()
    df["load_batch_id"] = str(uuid.uuid4())

    def _do_duckdb(c, data_df):
        c.execute("CREATE TABLE IF NOT EXISTS raw_prices_5m (symbol TEXT, datetime TIMESTAMP, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE, source_load_ts TIMESTAMP, load_batch_id TEXT, PRIMARY KEY (symbol, datetime))")
        c.register("df_tmp", data_df)
        c.execute("INSERT OR IGNORE INTO raw_prices_5m SELECT * FROM df_tmp")
        return c.execute("SELECT COUNT(*) FROM raw_prices_5m").fetchone()[0]

    def _do_postgres(c, data_df):
        # Ensure table exists
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS raw_prices_5m (
                symbol TEXT,
                datetime TIMESTAMP,
                open DOUBLE PRECISION,
                high DOUBLE PRECISION,
                low DOUBLE PRECISION,
                close DOUBLE PRECISION,
                volume DOUBLE PRECISION,
                source_load_ts TIMESTAMP,
                load_batch_id TEXT,
                PRIMARY KEY (symbol, datetime)
            )
        """))

        # Simple upsert using pandas to_sql and temporary table
        # For Postgres, we can use 'on conflict do nothing' but requires more complex SQL
        # or just use pandas to_sql with if_exists='append' if we don't care about duplicates
        # or handle duplicates by loading to a temp table first.

        from sqlalchemy import MetaData, Table
        metadata = MetaData()
        table = Table('raw_prices_5m', metadata, autoload_with=c.engine)

        # To handle 'INSERT OR IGNORE' equivalent in Postgres:
        from sqlalchemy.dialects.postgresql import insert

        records = data_df.to_dict(orient='records')
        for record in records:
            stmt = insert(table).values(record).on_conflict_do_nothing(index_elements=['symbol', 'datetime'])
            c.execute(stmt)

        return c.execute(text("SELECT COUNT(*) FROM raw_prices_5m")).fetchone()[0]

    if conn:
        if cfg.postgres_url:
            return _do_postgres(conn, df)
        return _do_duckdb(conn, df)

    with get_connection() as c:
        if cfg.postgres_url:
            return _do_postgres(c, df)
        return _do_duckdb(c, df)

def warmup_platform():
    cfg = get_config()
    warmup_pd = cfg.symbols_data.get("settings", {}).get("warmup_period", "60d")
    return load_prices_5m(period=warmup_pd)

def load_prices(): return load_prices_5m()
