import uuid
from datetime import datetime, timezone
from typing import Optional, List
import duckdb
import pandas as pd
import yfinance as yf
from sqlalchemy import text
from app.db.connection import get_duckdb_connection, get_connection
from app.config import get_config
from pathlib import Path

def fetch_prices_5m(symbols: List[str], period: str = None, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    if not symbols: return pd.DataFrame()

    if start_date:
        raw = yf.download(tickers=symbols, start=start_date, end=end_date, interval="5m", group_by="ticker", auto_adjust=True)
    else:
        period = period or "5d"
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

def save_to_bronze(df: pd.DataFrame, batch_id: str):
    """Save raw data to 'Data Lake' (Bronze layer) as Parquet."""
    if df.empty: return
    cfg = get_config()
    bronze_path = cfg.project_root / "data" / "bronze" / "prices_5m"
    bronze_path.mkdir(parents=True, exist_ok=True)

    file_path = bronze_path / f"batch_{batch_id}.parquet"
    df.to_parquet(file_path, index=False)
    return file_path

def log_etl_run(run_id: str, job_name: str, start_ts: datetime, end_ts: datetime, status: str, rows: int, error: str = None):
    cfg = get_config()
    if not cfg.postgres_url: return

    with get_connection() as conn:
        conn.execute(text("""
            INSERT INTO etl_log (run_id, job_name, start_ts, end_ts, status, rows_processed, error_message)
            VALUES (:run_id, :job_name, :start_ts, :end_ts, :status, :rows, :error)
        """), {
            "run_id": run_id,
            "job_name": job_name,
            "start_ts": start_ts,
            "end_ts": end_ts,
            "status": status,
            "rows": rows,
            "error": error
        })

def load_prices_5m(symbols=None, period=None, start_date=None, end_date=None, conn=None) -> int:
    cfg = get_config()
    start_ts = datetime.now(timezone.utc)
    batch_id = str(uuid.uuid4())
    job_name = f"yfinance_load_{period or 'historical'}"

    try:
        symbols = symbols or cfg.symbols_list
        period = period or cfg.default_period
        df = fetch_prices_5m(symbols, period=period, start_date=start_date, end_date=end_date)
        if df.empty:
            log_etl_run(batch_id, job_name, start_ts, datetime.utcnow(), "EMPTY", 0)
            return 0

        df["source_load_ts"] = datetime.utcnow()
        df["load_batch_id"] = batch_id

        # --- Bronze Layer: Save to Data Lake ---
        save_to_bronze(df, batch_id)

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

            # Use to_sql for reliable multi-symbol insert instead of manual insert to avoid reflection issues
            # We'll use a temporary table to handle 'ON CONFLICT DO NOTHING' equivalent
            temp_table = f"tmp_prices_{uuid.uuid4().hex[:8]}"
            data_df.to_sql(temp_table, c, if_exists="replace", index=False)

            c.execute(text(f"""
                INSERT INTO raw_prices_5m
                SELECT * FROM {temp_table}
                ON CONFLICT (symbol, datetime) DO NOTHING
            """))
            c.execute(text(f"DROP TABLE {temp_table}"))

            return c.execute(text("SELECT COUNT(*) FROM raw_prices_5m")).fetchone()[0]

        if conn:
            if cfg.postgres_url:
                res = _do_postgres(conn, df)
            else:
                res = _do_duckdb(conn, df)
            log_etl_run(batch_id, job_name, start_ts, datetime.utcnow(), "SUCCESS", res)
            return res

        with get_connection() as c:
            if cfg.postgres_url:
                res = _do_postgres(c, df)
            else:
                res = _do_duckdb(c, df)
            log_etl_run(batch_id, job_name, start_ts, datetime.utcnow(), "SUCCESS", res)
            return res
    except Exception as e:
        log_etl_run(batch_id, job_name, start_ts, datetime.utcnow(), "FAILED", 0, str(e))
        raise

def warmup_platform():
    cfg = get_config()
    warmup_pd = cfg.symbols_data.get("settings", {}).get("warmup_period", "60d")
    return load_prices_5m(period=warmup_pd)

def load_prices(): return load_prices_5m()
