"""Generic DB Schema and Helpers for User Stocks (Watchlist & Holdings)."""
from typing import Any, Dict, List, Optional
import duckdb
from app.db.connection import get_duckdb_connection

def init_user_tables():
    with get_duckdb_connection() as conn:
        # Create unified user_stocks table
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
        # Migrate existing data if tables exist
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
    with get_duckdb_connection() as conn:
        rows = conn.execute("""
            SELECT symbol, quantity, avg_cost, tags, note, updated_at
            FROM user_stocks
            ORDER BY
                CASE WHEN quantity > 0 THEN 0 ELSE 1 END,  -- Holdings first
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
    """Get symbols with quantity = 0."""
    with get_duckdb_connection() as conn:
        res = conn.execute("SELECT symbol FROM user_stocks WHERE quantity = 0 OR quantity IS NULL").fetchall()
        return [r[0] for r in res]

def get_holdings() -> List[Dict[str, Any]]:
    """Get holdings (quantity > 0)."""
    with get_duckdb_connection() as conn:
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
    """Add or update a stock in the unified table."""
    with get_duckdb_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO user_stocks (symbol, quantity, avg_cost, tags, note, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (symbol.upper(), quantity, avg_cost, tags, note))

def remove_stock(symbol: str):
    """Remove a stock from the unified table."""
    with get_duckdb_connection() as conn:
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
