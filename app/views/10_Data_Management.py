import streamlit as st
import subprocess
import pandas as pd
from datetime import datetime
from app.config import get_config
from app.db.connection import get_connection
from app.db.utils import init_user_tables
from app.core.etl.prices import load_prices_5m
from sqlalchemy import text

def run_dbt():
    try:
        # Run dbt against postgres
        result = subprocess.run(
            ["dbt", "run", "--profiles-dir", ".", "--profile", "postgres", "--target", "dev"],
            cwd="dbt",
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

st.title("⚙️ Data Management & ETL")

cfg = get_config()

# --- Connection Status ---
st.header("🔗 Connection Status")
col1, col2 = st.columns(2)

with col1:
    if cfg.postgres_url:
        st.success("Postgres: Configured")
    else:
        st.warning("Postgres: Not Configured (Falling back to DuckDB)")

with col2:
    try:
        with get_connection() as conn:
            if cfg.postgres_url:
                conn.execute(text("SELECT 1"))
            else:
                conn.execute("SELECT 1")
            st.success("Database: Connected")
    except Exception as e:
        st.error(f"Database: Connection Failed - {str(e)}")

# --- ETL Operations ---
st.header("📥 Market Data ETL (yfinance)")
st.write(f"Current symbols in watchlist: `{', '.join(cfg.symbols_list)}`")

col_etl1, col_etl2 = st.columns(2)

with col_etl1:
    period = st.selectbox("Select Period", ["1d", "5d", "1mo", "6mo", "1y"], index=1)
    if st.button("🚀 Refresh Market Data"):
        with st.spinner("Fetching data from yfinance and loading to Postgres..."):
            try:
                # Ensure tables exist
                init_user_tables()
                count = load_prices_5m(period=period)
                st.success(f"Successfully loaded {count} records!")
            except Exception as e:
                st.error(f"ETL Failed: {str(e)}")

# --- dbt Transformations ---
st.header("🔄 dbt Transformations")
st.write("Run dbt to calculate RSI, EMA, and other indicators in Postgres.")

if st.button("🛠️ Run dbt Transformations"):
    with st.spinner("Running dbt models..."):
        success, stdout, stderr = run_dbt()
        if success:
            st.success("dbt transformation complete!")
            with st.expander("Show dbt Output"):
                st.code(stdout)
        else:
            st.error("dbt transformation failed!")
            with st.expander("Show dbt Error"):
                st.code(stderr)

# --- Data Preview ---
st.header("📊 Data Preview")
try:
    with get_connection() as conn:
        if cfg.postgres_url:
            raw_count = conn.execute(text("SELECT COUNT(*) FROM raw_prices_5m")).fetchone()[0]
            st.metric("Raw Price Records", raw_count)

            df_preview = pd.read_sql("SELECT * FROM raw_prices_5m ORDER BY datetime DESC LIMIT 10", conn)
            st.subheader("Latest 10 Raw Records")
            st.dataframe(df_preview)

            # Check if marts exist
            try:
                marts_count = conn.execute(text("SELECT COUNT(*) FROM fct_financial_indicators")).fetchone()[0]
                st.metric("Transformed Records", marts_count)
                df_marts = pd.read_sql("SELECT * FROM fct_financial_indicators ORDER BY trade_datetime DESC LIMIT 10", conn)
                st.subheader("Latest 10 Transformed Records (RSI/EMA)")
                st.dataframe(df_marts)
            except:
                st.info("Run dbt transformations to see mart data.")
        else:
            st.info("Preview currently optimized for Postgres. Please configure POSTGRES_URL.")
except Exception as e:
    st.info("No data found or table not initialized yet. Run 'Refresh Market Data' first.")
