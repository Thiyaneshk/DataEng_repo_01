import uuid
from datetime import datetime
from typing import Optional, List
import duckdb
import pandas as pd
import yfinance as yf
from app.db.connection import get_duckdb_connection
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
    def _do(c):
        c.execute("CREATE TABLE IF NOT EXISTS raw_prices_5m (symbol TEXT, datetime TIMESTAMP, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE, source_load_ts TIMESTAMP, load_batch_id TEXT, PRIMARY KEY (symbol, datetime))")
        c.register("df_tmp", df)
        c.execute("INSERT OR IGNORE INTO raw_prices_5m SELECT * FROM df_tmp")
        return c.execute("SELECT COUNT(*) FROM raw_prices_5m").fetchone()[0]
    if conn: return _do(conn)
    with get_duckdb_connection() as c: return _do(c)

def warmup_platform():
    cfg = get_config()
    warmup_pd = cfg.symbols_data.get("settings", {}).get("warmup_period", "60d")
    return load_prices_5m(period=warmup_pd)

def load_prices(): return load_prices_5m()
