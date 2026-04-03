import streamlit as st
import duckdb
import plotly.graph_objects as go
from app.config import get_config

def main():
    st.title("📈 Stock Overview")
    cfg = get_config()
    with duckdb.connect(str(cfg.duckdb_path)) as conn:
        symbols = [s[0] for s in conn.execute("SELECT DISTINCT symbol FROM raw_prices_5m").fetchall()]
        if not symbols: st.warning("No data"); return
        sym = st.sidebar.selectbox("Symbol", symbols)
        df = conn.execute(f"SELECT * FROM raw_prices_5m WHERE symbol = '{sym}' ORDER BY datetime").df()
        fig = go.Figure(data=[go.Candlestick(x=df['datetime'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
