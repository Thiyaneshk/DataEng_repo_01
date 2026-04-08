"""Generic DB Schema and Helpers for User Stocks (Watchlist & Holdings)."""
from typing import Any, Dict, List, Optional
import duckdb
from sqlalchemy import text
from app.db.connection import get_duckdb_connection, get_connection, get_config

def init_user_tables():
    cfg = get_config()
    with get_connection() as conn:
        # Create unified user_stocks table
        if cfg.postgres_url:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS etl_log (
                    run_id TEXT PRIMARY KEY,
                    job_name TEXT,
                    start_ts TIMESTAMP,
                    end_ts TIMESTAMP,
                    status TEXT,
                    rows_processed INTEGER,
                    error_message TEXT
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_stocks (
                    symbol TEXT PRIMARY KEY,
                    quantity DOUBLE PRECISION DEFAULT 0,
                    avg_cost DOUBLE PRECISION,
                    tags TEXT,
                    note TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_stocks (
                    symbol TEXT PRIMARY KEY,
                    quantity DOUBLE DEFAULT 0,
                    avg_cost DOUBLE,
                    tags TEXT,
                    note TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        # Migrate existing data if tables exist (DuckDB only for now)
        if not cfg.postgres_url:
            migrate_legacy_data(conn)

def migrate_legacy_data(conn):
    """Migrate data from separate watchlist and holdings tables to unified user_stocks."""
    try:
        # Check if legacy tables exist
        watchlist_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='watchlist'").fetchone()
        holdings_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='holdings'").fetchone()

        if watchlist_exists:
            # Migrate watchlist (quantity=0)
            watchlist_data = conn.execute("SELECT symbol, tags, note FROM watchlist").fetchall()
            for symbol, tags, note in watchlist_data:
                conn.execute("""
                    INSERT OR IGNORE INTO user_stocks (symbol, quantity, avg_cost, tags, note)
                    VALUES (?, 0, NULL, ?, ?)
                """, (symbol, tags or "", note or ""))

        if holdings_exists:
            # Migrate holdings (quantity>0)
            holdings_data = conn.execute("SELECT symbol, quantity, avg_cost FROM holdings").fetchall()
            for symbol, quantity, avg_cost in holdings_data:
                conn.execute("""
                    INSERT OR REPLACE INTO user_stocks (symbol, quantity, avg_cost, tags, note, updated_at)
                    SELECT ?, ?, ?, COALESCE(tags, ''), COALESCE(note, ''), CURRENT_TIMESTAMP
                    FROM user_stocks WHERE symbol = ?
                """, (symbol, quantity, avg_cost, symbol))

        # Drop legacy tables after migration
        if watchlist_exists:
            conn.execute("DROP TABLE watchlist")
        if holdings_exists:
            conn.execute("DROP TABLE holdings")

    except Exception as e:
        # If migration fails, continue (tables might not exist)
        pass

def get_all_stocks() -> List[Dict[str, Any]]:
    """Get all user stocks (watchlist + holdings)."""
    cfg = get_config()
    with get_connection() as conn:
        sql = """
            SELECT symbol, quantity, avg_cost, tags, note, updated_at
            FROM user_stocks
            ORDER BY
                CASE WHEN quantity > 0 THEN 0 ELSE 1 END,  -- Holdings first
                updated_at DESC
        """
        if cfg.postgres_url:
            rows = conn.execute(text(sql)).fetchall()
        else:
            rows = conn.execute(sql).fetchall()

        return [
            {
                "symbol": r[0],
                "quantity": r[1] or 0,
                "avg_cost": r[2],
                "tags": r[3] or "",
                "note": r[4] or "",
                "updated_at": r[5],
                "is_holding": (r[1] or 0) > 0,
            }
            for r in rows
        ]

def get_watchlist_symbols() -> List[str]:
    """Get symbols with quantity = 0."""
    cfg = get_config()
    with get_connection() as conn:
        sql = "SELECT symbol FROM user_stocks WHERE quantity = 0 OR quantity IS NULL"
        if cfg.postgres_url:
            res = conn.execute(text(sql)).fetchall()
        else:
            res = conn.execute(sql).fetchall()
        return [r[0] for r in res]

def get_holdings() -> List[Dict[str, Any]]:
    """Get holdings (quantity > 0)."""
    cfg = get_config()
    with get_connection() as conn:
        sql = """
            SELECT symbol, quantity, avg_cost, updated_at
            FROM user_stocks
            WHERE quantity > 0
            ORDER BY updated_at DESC
        """
        if cfg.postgres_url:
            rows = conn.execute(text(sql)).fetchall()
        else:
            rows = conn.execute(sql).fetchall()

        return [
            {
                "symbol": r[0],
                "quantity": r[1],
                "avg_cost": r[2],
                "updated_at": r[3],
            }
            for r in rows
        ]

def add_or_update_stock(symbol: str, quantity: float = 0, avg_cost: Optional[float] = None,
                       tags: str = "", note: str = ""):
    """Add or update a stock in the unified table."""
    cfg = get_config()
    from datetime import datetime, timezone
    with get_connection() as conn:
        if cfg.postgres_url:
            sql = text("""
                INSERT INTO user_stocks (symbol, quantity, avg_cost, tags, note, updated_at)
                VALUES (:symbol, :quantity, :avg_cost, :tags, :note, :updated_at)
                ON CONFLICT (symbol) DO UPDATE SET
                    quantity = EXCLUDED.quantity,
                    avg_cost = EXCLUDED.avg_cost,
                    tags = EXCLUDED.tags,
                    note = EXCLUDED.note,
                    updated_at = EXCLUDED.updated_at
            """)
            conn.execute(sql, {
                "symbol": symbol.upper(),
                "quantity": quantity,
                "avg_cost": avg_cost,
                "tags": tags,
                "note": note,
                "updated_at": datetime.now(timezone.utc)
            })
        else:
            conn.execute("""
                INSERT OR REPLACE INTO user_stocks (symbol, quantity, avg_cost, tags, note, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (symbol.upper(), quantity, avg_cost, tags, note))

def remove_stock(symbol: str):
    """Remove a stock from the unified table."""
    cfg = get_config()
    with get_connection() as conn:
        sql = "DELETE FROM user_stocks WHERE symbol = :symbol"
        if cfg.postgres_url:
            conn.execute(text(sql), {"symbol": symbol.upper()})
        else:
            conn.execute("DELETE FROM user_stocks WHERE symbol = ?", (symbol.upper(),))

# Legacy functions for backward compatibility
def get_watchlist() -> List[Dict[str, Any]]:
    """Legacy: Get watchlist items."""
    stocks = get_all_stocks()
    return [s for s in stocks if not s["is_holding"]]

def add_to_watchlist(symbol: str, tags: str = "", note: str = ""):
    """Legacy: Add to watchlist (quantity=0)."""
    add_or_update_stock(symbol, quantity=0, tags=tags, note=note)

def remove_from_watchlist(symbol: str):
    """Legacy: Remove from watchlist."""
    remove_stock(symbol)

def update_holding(symbol: str, quantity: float, avg_cost: float):
    """Legacy: Update holding."""
    add_or_update_stock(symbol, quantity=quantity, avg_cost=avg_cost)

def remove_holding(symbol: str):
    """Legacy: Remove holding."""
    remove_stock(symbol)
