import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from app.config import get_config
from app.db.connection import get_connection
from sqlalchemy import text

def main():
    st.title("📈 Stock Overview")
    cfg = get_config()
    with get_connection() as conn:
        if cfg.postgres_url:
            symbols_query = text("SELECT DISTINCT symbol FROM raw_prices_5m ORDER BY symbol")
            symbols = [s[0] for s in conn.execute(symbols_query).fetchall()]
        else:
            symbols = [s[0] for s in conn.execute("SELECT DISTINCT symbol FROM raw_prices_5m ORDER BY symbol").fetchall()]

        if not symbols:
            st.warning("No data found. Please load data from the Admin page.")
            return

        sym = st.sidebar.selectbox("Symbol", symbols)

        if cfg.postgres_url:
            query = text("SELECT * FROM raw_prices_5m WHERE symbol = :sym ORDER BY datetime")
            df = pd.read_sql(query, conn, params={"sym": sym})
        else:
            df = conn.execute(f"SELECT * FROM raw_prices_5m WHERE symbol = '{sym}' ORDER BY datetime").df()

        fig = go.Figure(data=[go.Candlestick(
            x=df['datetime'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )])

        # Remove weekend gaps
        fig.update_xaxes(rangebreaks=[
            dict(bounds=["sat", "mon"]), # hide weekends
        ])

        fig.update_layout(title=f"{sym} Price Action", xaxis_title="Time", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
