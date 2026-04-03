"""Generic DB Schema and Helpers for Watchlist and Holdings."""
from typing import List
import duckdb
from app.db.connection import get_duckdb_connection

def init_user_tables():
    with get_duckdb_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                symbol TEXT PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT,
                note TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                symbol TEXT PRIMARY KEY,
                quantity DOUBLE,
                avg_cost DOUBLE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

def get_watchlist_symbols() -> List[str]:
    try:
        with get_duckdb_connection() as conn:
            res = conn.execute("SELECT symbol FROM watchlist").fetchall()
            return [r[0] for r in res]
    except Exception:
        return []

def add_to_watchlist(symbol: str, tags: str = "", note: str = ""):
    with get_duckdb_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO watchlist (symbol, tags, note) VALUES (?, ?, ?)",
                     (symbol.upper(), tags, note))

def remove_from_watchlist(symbol: str):
    with get_duckdb_connection() as conn:
        conn.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol.upper(),))

def update_holding(symbol: str, quantity: float, avg_cost: float):
    with get_duckdb_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO holdings (symbol, quantity, avg_cost, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                     (symbol.upper(), quantity, avg_cost))
