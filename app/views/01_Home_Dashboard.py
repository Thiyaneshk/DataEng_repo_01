import streamlit as st
import duckdb
from app.config import get_config

def main():
    st.title("🏠 Home Dashboard")
    cfg = get_config()
    try:
        with duckdb.connect(str(cfg.duckdb_path)) as conn:
            count = conn.execute("SELECT COUNT(*) FROM raw_prices_5m").fetchone()[0]
            st.metric("Canonical 5m Rows", f"{count:,}")
    except Exception:
        st.warning("No data found. Run ETL via Admin or CLI.")

if __name__ == "__main__":
    main()
