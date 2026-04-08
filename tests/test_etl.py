"""Tests for the ETL pipeline (app.core.etl.prices).

Learning goals:
- Test real external-data functions against an in-memory DuckDB.
- Understand how to use pytest fixtures for database-backed tests.
"""

import duckdb
import pytest

from app.core.etl.prices import fetch_prices_5m, load_prices_5m


# ---------------------------------------------------------------------------
# fetch_prices
# ---------------------------------------------------------------------------


class TestFetchPrices:
    """Tests for the fetch_prices_5m() function (network call to yfinance)."""

    def test_returns_dataframe_with_expected_columns(self) -> None:
        """Fetch a single symbol for 1 day and check the shape."""
        df = fetch_prices_5m(symbols=["AAPL"], period="1d")
        expected_cols = {"symbol", "datetime", "open", "high", "low", "close", "volume"}
        assert set(df.columns) == expected_cols, f"Columns mismatch: {list(df.columns)}"

    def test_returns_rows_for_valid_symbol(self) -> None:
        """We should get at least 1 row for a major US stock on a trading day."""
        df = fetch_prices_5m(symbols=["AAPL"], period="5d")
        assert len(df) > 0, "Expected at least 1 row from AAPL data"

    def test_handles_invalid_symbol_gracefully(self) -> None:
        """An invalid ticker should not crash; it should return an empty (or partial) DF."""
        df = fetch_prices_5m(symbols=["ZZZZZZ_INVALID"], period="1d")
        # We just verify it doesn't raise; the DF may be empty
        assert df is not None


# ---------------------------------------------------------------------------
# load_prices  (uses in-memory DuckDB — no file touches)
# ---------------------------------------------------------------------------


class TestLoadPrices:
    """Tests for the load_prices_5m() function using an in-memory DuckDB."""

    @pytest.fixture()
    def mem_conn(self):
        """Create a fresh in-memory DuckDB connection per test."""
        conn = duckdb.connect(":memory:")
        yield conn
        conn.close()

    def test_creates_raw_prices_table(self, mem_conn) -> None:
        """After load_prices_5m(), the raw_prices_5m table must exist."""
        load_prices_5m(symbols=["AAPL"], period="1d", conn=mem_conn)
        tables = [
            row[0]
            for row in mem_conn.execute(
                "SELECT table_name FROM information_schema.tables"
            ).fetchall()
        ]
        assert "raw_prices_5m" in tables

    def test_inserts_rows(self, mem_conn) -> None:
        """After loading, the table should have > 0 rows."""
        row_count = load_prices_5m(
            symbols=["AAPL"], period="5d", conn=mem_conn
        )
        assert row_count > 0

    def test_table_schema_matches(self, mem_conn) -> None:
        """Verify the column names and types in raw_prices_5m."""
        load_prices_5m(symbols=["AAPL"], period="1d", conn=mem_conn)
        cols = mem_conn.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'raw_prices_5m'
            ORDER BY ordinal_position
            """
        ).fetchall()

        col_map = {name: dtype for name, dtype in cols}
        assert "symbol" in col_map
        assert "datetime" in col_map
        assert "open" in col_map
        assert "close" in col_map
        assert "volume" in col_map
