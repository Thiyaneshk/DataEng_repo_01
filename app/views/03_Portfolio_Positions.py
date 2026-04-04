import streamlit as st
import duckdb
import pandas as pd
from app.config import get_config

def main():
    st.title("💼 Portfolio Positions")
    cfg = get_config()

    with duckdb.connect(str(cfg.duckdb_path)) as conn:
        try:
            holdings_df = conn.execute("SELECT * FROM holdings").df()
        except Exception:
            holdings_df = pd.DataFrame()

        if holdings_df.empty:
            st.info("No positions recorded yet. Add them in Admin.")
            return

        prices_df = conn.execute(
            """
            SELECT symbol, close
            FROM (
                SELECT symbol, close,
                       ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY datetime DESC) AS row_num
                FROM raw_prices_5m
            )
            WHERE row_num = 1
            """
        ).df()

    if not prices_df.empty:
        holdings_df = holdings_df.merge(prices_df, on="symbol", how="left")
    else:
        holdings_df["close"] = None

    holdings_df["market_value"] = holdings_df["quantity"] * holdings_df["close"].fillna(0)
    holdings_df["market_value"] = holdings_df["market_value"].round(2)
    holdings_df["unrealized_pnl"] = (
        holdings_df["market_value"] - holdings_df["quantity"] * holdings_df["avg_cost"]
    ).round(2)

    st.dataframe(holdings_df, use_container_width=True)

    if holdings_df["close"].isnull().any():
        st.warning(
            "Some holdings have no price data yet. Run the ETL pipeline or add symbol price data to DuckDB."
        )

    total_value = holdings_df["market_value"].sum()
    st.metric("Total portfolio value", f"${total_value:,.2f}")

if __name__ == "__main__":
    main()
