import streamlit as st
import duckdb
from app.config import get_config

def main():
    st.title("💼 Portfolio Positions")
    cfg = get_config()
    with duckdb.connect(str(cfg.duckdb_path)) as conn:
        try:
            df = conn.execute("SELECT * FROM holdings").df()
            st.dataframe(df, use_container_width=True)
        except Exception:
            st.info("No positions recorded yet. Add them in Admin.")

if __name__ == "__main__":
    main()
