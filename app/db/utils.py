"""Generic DB Schema and Helpers for User Stocks (Watchlist & Holdings)."""
from typing import Any, Dict, List, Optional
from sqlalchemy import text

from app.config import get_config
from app.db.connection import get_connection


def init_user_tables():
    """Initialize user_stocks table (already created in Postgres)."""
    cfg = get_config()
    if not cfg.postgres_url:
        # Only for DuckDB fallback
        from app.db.connection import get_duckdb_connection
        with get_duckdb_connection() as conn:
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


def migrate_legacy_data(conn):
    """Migrate data from separate watchlist and holdings tables to unified user_stocks (legacy)."""
    # No longer needed with Postgres - tables are pre-created
    pass

def get_all_stocks() -> List[Dict[str, Any]]:
    """Get all user stocks (watchlist + holdings) from Postgres."""
    cfg = get_config()
    with get_connection() as conn:
        if cfg.postgres_url:
            result = conn.execute(text("""
                SELECT symbol, quantity, avg_cost, tags, note, updated_at
                FROM user_stocks
                ORDER BY
                    CASE WHEN quantity > 0 THEN 0 ELSE 1 END,
                    updated_at DESC
            """))
            rows = result.fetchall()
        else:
            rows = conn.execute("""
                SELECT symbol, quantity, avg_cost, tags, note, updated_at
                FROM user_stocks
                ORDER BY
                    CASE WHEN quantity > 0 THEN 0 ELSE 1 END,
                    updated_at DESC
            """).fetchall()

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
    """Get symbols with quantity = 0 (watchlist only)."""
    cfg = get_config()
    with get_connection() as conn:
        if cfg.postgres_url:
            result = conn.execute(text("""
                SELECT symbol FROM user_stocks 
                WHERE quantity = 0 OR quantity IS NULL
            """))
            res = result.fetchall()
        else:
            res = conn.execute("SELECT symbol FROM user_stocks WHERE quantity = 0 OR quantity IS NULL").fetchall()

        return [r[0] for r in res]


def get_holdings() -> List[Dict[str, Any]]:
    """Get holdings (quantity > 0)."""
    cfg = get_config()
    with get_connection() as conn:
        if cfg.postgres_url:
            result = conn.execute(text("""
                SELECT symbol, quantity, avg_cost, updated_at
                FROM user_stocks
                WHERE quantity > 0
                ORDER BY updated_at DESC
            """))
            rows = result.fetchall()
        else:
            rows = conn.execute("""
                SELECT symbol, quantity, avg_cost, updated_at
                FROM user_stocks
                WHERE quantity > 0
                ORDER BY updated_at DESC
            """).fetchall()

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
    """Add or update a stock in user_stocks."""
    cfg = get_config()
    with get_connection() as conn:
        if cfg.postgres_url:
            conn.execute(text("""
                INSERT INTO user_stocks (symbol, quantity, avg_cost, tags, note, updated_at)
                VALUES (:symbol, :quantity, :avg_cost, :tags, :note, CURRENT_TIMESTAMP)
                ON CONFLICT (symbol) DO UPDATE SET
                    quantity = :quantity,
                    avg_cost = :avg_cost,
                    tags = :tags,
                    note = :note,
                    updated_at = CURRENT_TIMESTAMP
            """), {
                "symbol": symbol.upper(),
                "quantity": quantity,
                "avg_cost": avg_cost,
                "tags": tags,
                "note": note
            })
            conn.commit()
        else:
            conn.execute("""
                INSERT OR REPLACE INTO user_stocks (symbol, quantity, avg_cost, tags, note, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (symbol.upper(), quantity, avg_cost, tags, note))


def remove_stock(symbol: str):
    """Remove a stock from user_stocks."""
    cfg = get_config()
    with get_connection() as conn:
        if cfg.postgres_url:
            conn.execute(text("DELETE FROM user_stocks WHERE symbol = :symbol"), {"symbol": symbol.upper()})
            conn.commit()
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

