import streamlit as st
import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime
from app.config import get_config
from app.db.connection import get_connection
from app.db.utils import init_user_tables
from app.core.etl.prices import load_prices_5m
from sqlalchemy import text

def run_dbt(install_deps=False):
    try:
        # 1. Install dependencies if requested or missing
        dbt_deps_path = Path("dbt/dbt_packages")
        if install_deps or not dbt_deps_path.exists():
            deps = subprocess.run(
                ["dbt", "deps", "--profiles-dir", "."],
                cwd="dbt",
                capture_output=True,
                text=True
            )
            if deps.returncode != 0:
                return False, deps.stdout, deps.stderr

        # 2. Run dbt against postgres
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
    etl_type = st.radio("Load Type", ["Recent (Period)", "Historical (Backfill)"])

    if etl_type == "Recent (Period)":
        period = st.selectbox("Select Period", ["1d", "5d", "1mo", "6mo", "1y"], index=1)
        if st.button("🚀 Refresh Market Data"):
            with st.spinner("Fetching data and loading..."):
                try:
                    init_user_tables()
                    count = load_prices_5m(period=period)
                    st.success(f"Successfully loaded {count} records!")
                except Exception as e:
                    st.error(f"ETL Failed: {str(e)}")
    else:
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input("Start Date", value=datetime(2024, 1, 1))
        with col_end:
            end_date = st.date_input("End Date", value=datetime.now())

        if st.button("📅 Run Historical Backfill"):
            with st.spinner(f"Backfilling from {start_date} to {end_date}..."):
                try:
                    init_user_tables()
                    count = load_prices_5m(start_date=start_date.strftime("%Y-%m-%d"),
                                         end_date=end_date.strftime("%Y-%m-%d"))
                    st.success(f"Successfully backfilled {count} records!")
                except Exception as e:
                    st.error(f"Backfill Failed: {str(e)}")

# --- dbt Transformations ---
st.header("🔄 dbt Transformations")
st.write("Run dbt to calculate RSI, EMA, and other indicators in Postgres.")

col_dbt1, col_dbt2 = st.columns([1, 4])
with col_dbt1:
    install_deps = st.checkbox("Install Deps", value=False)
with col_dbt2:
    if st.button("🛠️ Run dbt Transformations"):
        with st.spinner("Running dbt models..."):
            success, stdout, stderr = run_dbt(install_deps=install_deps)
        if success:
            st.success("dbt transformation complete!")
            with st.expander("Show dbt Output"):
                st.code(stdout)
        else:
            st.error("dbt transformation failed!")
            with st.expander("Show dbt Error"):
                st.code(stderr)

# --- Pipeline Observability ---
st.header("🕵️ Pipeline Observability")
try:
    with get_connection() as conn:
        if cfg.postgres_url:
            st.subheader("Recent ETL Runs")
            df_logs = pd.read_sql(text("SELECT * FROM etl_log ORDER BY start_ts DESC LIMIT 10"), conn)
            st.dataframe(df_logs)
except Exception:
    st.info("No ETL logs found. Run a refresh to see them.")

# --- Data Preview ---
st.header("📊 Data Preview")
try:
    with get_connection() as conn:
        if cfg.postgres_url:
            raw_count = conn.execute(text("SELECT COUNT(*) FROM raw_prices_5m")).fetchone()[0]
            st.metric("Raw Price Records", raw_count)

            df_preview = pd.read_sql(text("SELECT * FROM raw_prices_5m ORDER BY datetime DESC LIMIT 10"), conn)
            st.subheader("Latest 10 Raw Records")
            st.dataframe(df_preview)

            # Check if marts exist
            try:
                marts_count = conn.execute(text("SELECT COUNT(*) FROM fct_financial_indicators")).fetchone()[0]
                st.metric("Transformed Records", marts_count)
                df_marts = pd.read_sql(text("SELECT * FROM fct_financial_indicators ORDER BY trade_datetime DESC LIMIT 10"), conn)
                st.subheader("Latest 10 Transformed Records (RSI/EMA)")
                st.dataframe(df_marts)
            except:
                st.info("Run dbt transformations to see mart data.")
        else:
            st.info("Preview currently optimized for Postgres. Please configure POSTGRES_URL.")
except Exception as e:
    st.info("No data found or table not initialized yet. Run 'Refresh Market Data' first.")
